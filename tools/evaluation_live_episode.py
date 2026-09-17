#!/usr/bin/env python3
"""Durable policy execution for live real-world evaluation episodes.

The runner composes the single-attempt live worker adapter with frozen B0, B1
and B2 policy decisions. It persists dispatch intent before each external side
effect. A later process that finds an in-flight dispatch never repeats it: the
allowance stays held and the episode stops for operator reconciliation.

The Controller uses a live adapter by default. Tests may inject scripted
adapters or explicitly disable it to exercise the launch-blocking path.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "test" / "harness"))

import acceptance  # noqa: E402
import evaluation_live_controller  # noqa: E402
import evaluation_live_worker  # noqa: E402
import evaluation_runner  # noqa: E402
import realworld  # noqa: E402
import validate_records  # noqa: E402
from dispatch_budget import BudgetError, DispatchBudget  # noqa: E402

DEFAULT_OUTPUT = ROOT / "test" / "results" / "2026-09-17-live-episode-integration.json"
DEFAULT_REPORT = ROOT / "test" / "results" / "2026-09-17-live-episode-integration.md"
EPISODE_BUDGET_USD = 4.0
MAX_ACTIONS = 6
LOGICAL_TIME = "2026-09-17T00:00:00+00:00"
POLICY_DIR = ROOT / "test" / "fixtures" / "realworld" / "policies"
CAPS_USD = {
    "worker-sonnet-low": 0.75,
    "worker-opus-high": 1.50,
    "controller": 3.25,
}
MINIMUM_USD = 0.01


class LiveEpisodeError(RuntimeError):
    """Invalid episode state or adapter result."""


class ControllerAdapter(Protocol):
    """Boundary for live or scripted Controller implementations."""

    def run(self, request: evaluation_live_controller.ControllerRequest) -> dict:
        """Return a terminal Controller outcome and provider accounting."""


_DEFAULT_CONTROLLER = object()


@dataclasses.dataclass(frozen=True)
class LiveEpisodeSpec:
    episode_id: str
    task_id: str
    policy_id: str
    sensitivity: str = "structured"
    horizon: str = "medium"
    blast: str = "contained"
    self_directed: bool = False
    budget_usd: float = EPISODE_BUDGET_USD


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_plan(spec: LiveEpisodeSpec) -> dict:
    """Load `plan` from the candidate bundle rather than development source."""
    tools_dir = ROOT / "dist" / "tools"
    module_path = tools_dir / "route.py"
    name = "evaluation_frozen_route"
    loaded = sys.modules.get(name)
    if loaded is None:
        module_spec = importlib.util.spec_from_file_location(name, module_path)
        if module_spec is None or module_spec.loader is None:
            raise LiveEpisodeError(f"cannot load frozen router: {module_path}")
        loaded = importlib.util.module_from_spec(module_spec)
        sys.modules[name] = loaded
        sys.path.insert(0, str(tools_dir))
        prior_bytecode_setting = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            module_spec.loader.exec_module(loaded)
        finally:
            sys.dont_write_bytecode = prior_bytecode_setting
            sys.path.remove(str(tools_dir))
    return loaded.plan(spec.sensitivity, spec.horizon, spec.blast,
                       spec.self_directed, ledger=[])


class PolicyExecutor:
    """Choose the next action from policy, frozen route output and observations.

    The decision boundary deliberately receives no task identity, source
    project, hidden grade or reference repair.
    """

    def __init__(self, policy_id: str, route_plan: dict):
        if policy_id not in {"B0", "B1", "B2"}:
            raise ValueError(f"unsupported policy: {policy_id}")
        self.policy_id = policy_id
        self.route_plan = route_plan

    @staticmethod
    def _worker(cell: str, reason: str, guidance: str | None = None) -> dict:
        return {"kind": "worker", "requested_cell": cell,
                "reason": reason, "guidance": guidance}

    @staticmethod
    def _controller(reason: str) -> dict:
        return {"kind": "controller", "requested_cell": "controller",
                "reason": reason, "guidance": None}

    @staticmethod
    def _stop(reason: str) -> dict:
        return {"kind": "stop", "reason": reason}

    def decide(self, history: list[dict]) -> dict:
        if len(history) >= MAX_ACTIONS:
            return self._stop("action_limit")
        if history and history[-1].get("kind") == "worker" and history[-1].get("public_passed"):
            return self._stop("visible_acceptance_passed")
        if self.policy_id == "B0":
            return self._b0(history)
        if self.policy_id == "B1":
            return self._b1(history)
        return self._b2(history)

    def _b0(self, history: list[dict]) -> dict:
        workers = [row for row in history if row.get("kind") == "worker"]
        sequence = (
            ("worker-sonnet-low", "fixed_floor"),
            ("worker-sonnet-low", "one_local_repair"),
            ("worker-opus-high", "fixed_fallback"),
        )
        if len(workers) >= len(sequence):
            return self._stop("fixed_fallback_exhausted")
        cell, reason = sequence[len(workers)]
        return self._worker(cell, reason)

    def _b1(self, history: list[dict]) -> dict:
        workers = [row for row in history if row.get("kind") == "worker"]
        controllers = [row for row in history if row.get("kind") == "controller"]
        if not history:
            first = self.route_plan["first"]
            return (self._controller("frozen_route_proactive") if first == "controller"
                    else self._worker(first, "frozen_route_first"))
        if history[-1].get("kind") == "controller":
            controller = history[-1]
            if controller.get("controller_outcome") == "solution":
                return self._worker("worker-sonnet-low", "apply_controller_solution",
                                    controller.get("guidance"))
            return self._worker("worker-opus-high", "controller_fallback")
        tried = {row.get("requested_cell") for row in workers}
        ladder = self.route_plan.get("execution_ladder") or self.route_plan.get("ladder") or []
        next_cell = next((cell for cell in ladder if cell not in tried), None)
        if next_cell:
            return self._worker(next_cell, "next_frozen_route_rung")
        if not controllers:
            return self._controller("frozen_route_ladder_exhausted")
        return self._stop("frozen_route_escalation_exhausted")

    def _b2(self, history: list[dict]) -> dict:
        workers = [row for row in history if row.get("kind") == "worker"]
        controllers = [row for row in history if row.get("kind") == "controller"]
        if not history:
            return self._worker("worker-sonnet-low", "economical_floor")
        if history[-1].get("kind") == "controller":
            controller = history[-1]
            if controller.get("controller_outcome") == "solution":
                return self._worker("worker-sonnet-low", "apply_controller_solution",
                                    controller.get("guidance"))
            return self._worker("worker-opus-high", "controller_fallback")
        if not controllers and len(workers) == 1:
            return self._worker("worker-sonnet-low", "one_local_repair")
        if not controllers:
            distinct = {row.get("actor_digest") for row in workers if row.get("actor_digest")}
            cross_module = any(row.get("cross_module_conflict") is True for row in workers)
            if len(distinct) >= 2 or cross_module:
                return self._controller("observable_escalation_trigger")
            return self._stop("repeated_hypothesis_without_new_evidence")
        if not any(row.get("requested_cell") == "worker-opus-high" for row in workers):
            return self._worker("worker-opus-high", "post_controller_fallback")
        return self._stop("observable_policy_exhausted")


class LiveEpisodeRunner:
    """Run or resume one live episode with durable at-most-once dispatch."""

    def __init__(self, campaign_root: Path, worker_adapter=None,
                 controller_adapter: ControllerAdapter | None | object = _DEFAULT_CONTROLLER):
        self.root = campaign_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.worker = worker_adapter or evaluation_live_worker.LiveWorkerAdapter()
        self.controller = (evaluation_live_controller.LiveControllerAdapter()
                           if controller_adapter is _DEFAULT_CONTROLLER else controller_adapter)
        catalogue = realworld.load_catalogue()
        self.tasks = {task["id"]: task for task in realworld.ready_tasks(catalogue)}
        self.catalogue = catalogue
        self.bundle = json.loads((ROOT / "dist" / "bundle-manifest.json").read_text(encoding="utf-8"))

    def _paths(self, spec: LiveEpisodeSpec) -> dict[str, Path]:
        base = self.root / spec.episode_id
        return {"base": base, "actor": base / "actor", "state": base / "state.json",
                "events": base / "events.jsonl", "budget": base / "dispatch-budget.json",
                "ledger": base / "routing-ledger.jsonl",
                "controllers": base / "controller-workspaces"}

    def _save(self, paths: dict[str, Path], state: dict, stage: str,
              event: str, details: dict) -> None:
        transition = {"stage": stage, "event": event, "details": details}
        transition["id"] = digest(transition)
        state["pending_transition"] = transition
        evaluation_runner.atomic_json(paths["state"], state)
        self._recover_transition(paths, state)

    @staticmethod
    def _recover_transition(paths: dict[str, Path], state: dict) -> None:
        transition = state.get("pending_transition")
        if not transition:
            return
        matches = [row for row in evaluation_runner.read_events(paths["events"])
                   if (row.get("details") or {}).get("transition_id") == transition["id"]]
        if len(matches) > 1:
            raise LiveEpisodeError(f"duplicate transition: {transition['id']}")
        if not matches:
            evaluation_runner.append_event(
                paths["events"], transition["event"],
                {**transition["details"], "transition_id": transition["id"]},
            )
        state["stage"] = transition["stage"]
        state.pop("pending_transition", None)
        evaluation_runner.atomic_json(paths["state"], state)

    def _initialise(self, spec: LiveEpisodeSpec, paths: dict[str, Path]) -> dict:
        spec_hash = digest(dataclasses.asdict(spec))
        if paths["state"].is_file():
            state = json.loads(paths["state"].read_text(encoding="utf-8"))
            if state.get("spec_sha256") != spec_hash:
                raise LiveEpisodeError("checkpoint belongs to a different episode specification")
            self._recover_transition(paths, state)
            return state
        if spec.task_id not in self.tasks:
            raise ValueError(f"task is not ready: {spec.task_id}")
        if spec.policy_id not in {"B0", "B1", "B2"}:
            raise ValueError(f"unknown policy: {spec.policy_id}")
        task = self.tasks[spec.task_id]
        paths["base"].mkdir(parents=True)
        shutil.copytree(realworld.FIXTURES / task["repo"], paths["actor"])
        policy_path = POLICY_DIR / f"{spec.policy_id}.json"
        route_plan = load_frozen_plan(spec)
        baseline = realworld.actor_hashes(paths["actor"])
        state = {
            "schema_version": 1, "stage": "ready", "spec_sha256": spec_hash,
            "route_plan": route_plan, "history": [], "baseline": baseline,
            "manifest": {
                "campaign": self.catalogue["campaign"], "task_id": spec.task_id,
                "policy_id": spec.policy_id, "policy_sha256": file_sha256(policy_path),
                "bundle_version": self.bundle["bundle_version"],
                "frozen_route_sha256": file_sha256(ROOT / "dist" / "tools" / "route.py"),
                "episode_budget_usd": spec.budget_usd,
            },
        }
        self._save(paths, state, "ready", "episode_initialised", state["manifest"])
        return state

    def _recover_dispatched(self, paths: dict[str, Path], state: dict,
                            budget: DispatchBudget) -> dict:
        action = state["current_action"]
        invocation_id = action["invocation_id"]
        row = budget.snapshot()["invocations"][invocation_id]
        if row["state"] == "running":
            budget.settle(invocation_id, None, final=False,
                          telemetry={"status": "interrupted", "recovered": True},
                          evidence="recovery-no-terminal-envelope")
        elif row["state"] not in {"uncertain", "settled"}:
            raise LiveEpisodeError(f"cannot recover dispatched budget state: {row['state']}")
        state["stop_reason"] = "in_flight_dispatch_requires_reconciliation"
        self._save(paths, state, "blocked", "dispatch_recovery_blocked", {
            "invocation_id": invocation_id,
            "allowance_retained": row["state"] != "settled",
            "provider_called": False,
        })
        return self.summary(spec=None, paths=paths, state=state, budget=budget)

    def run(self, spec: LiveEpisodeSpec) -> dict:
        paths = self._paths(spec)
        state = self._initialise(spec, paths)
        budget = DispatchBudget(paths["budget"], spec.budget_usd if not paths["budget"].exists() else None)
        if state["stage"] == "action_dispatched":
            return self._recover_dispatched(paths, state, budget)
        if state["stage"] in {"complete", "blocked"}:
            return self.summary(spec, paths, state, budget)
        executor = PolicyExecutor(spec.policy_id, state["route_plan"])
        task = self.tasks[spec.task_id]

        while state["stage"] not in {"complete", "blocked"}:
            if state["stage"] == "ready":
                action = executor.decide(state["history"])
                if action["kind"] == "stop":
                    state["stop_reason"] = action["reason"]
                    self._save(paths, state, "terminated", "policy_stopped", {
                        "reason": action["reason"], "hidden_grade_seen": False,
                    })
                    continue
                if action["kind"] == "controller" and self.controller is None:
                    state["stop_reason"] = "live_controller_adapter_missing"
                    self._save(paths, state, "blocked", "controller_unavailable", {
                        "reason": state["stop_reason"], "provider_called": False,
                    })
                    continue
                sequence = len(state["history"]) + 1
                action.update(sequence=sequence,
                              invocation_id=f"inv-{spec.episode_id}-{sequence:03d}")
                state["current_action"] = action
                self._save(paths, state, "action_planned", "action_planned", {
                    "sequence": sequence, "kind": action["kind"],
                    "requested_cell": action["requested_cell"], "reason": action["reason"],
                })
                continue

            if state["stage"] == "action_planned":
                action = state["current_action"]
                try:
                    allowance = budget.reserve(
                        action["invocation_id"], CAPS_USD[action["requested_cell"]], MINIMUM_USD,
                        {"episode_id": spec.episode_id, "policy_id": spec.policy_id,
                         "sequence": action["sequence"], "requested_cell": action["requested_cell"]},
                    )
                except BudgetError as exc:
                    state["stop_reason"] = "next_reservation_does_not_fit"
                    self._save(paths, state, "blocked", "budget_blocked", {
                        "reason": state["stop_reason"], "detail": str(exc),
                    })
                    continue
                action["allowance_usd"] = allowance
                self._save(paths, state, "action_reserved", "action_reserved", {
                    "invocation_id": action["invocation_id"], "allowance_usd": allowance,
                })
                continue

            if state["stage"] == "action_reserved":
                action = state["current_action"]
                accounting_state = budget.snapshot()["invocations"][action["invocation_id"]]["state"]
                if accounting_state != "reserved":
                    return self._recover_dispatched(paths, state, budget)
                budget.start(action["invocation_id"])
                self._save(paths, state, "action_dispatched", "action_dispatched", {
                    "invocation_id": action["invocation_id"],
                    "requested_cell": action["requested_cell"],
                })
                outcome = self._invoke(spec, task, paths, action, state["history"])
                actor_snapshot = evaluation_runner.tree_snapshot(paths["actor"])
                state["pending_outcome"] = outcome
                state["pending_actor_snapshot"] = actor_snapshot
                self._save(paths, state, "action_committed", "action_result_committed", {
                    "invocation_id": action["invocation_id"],
                    "terminal": outcome.get("terminal") is True,
                    "cost_known": outcome.get("cost_usd") is not None,
                    "actor_digest": actor_snapshot["digest"],
                })
                continue

            if state["stage"] == "action_committed":
                self._reconcile_action(spec, task, paths, state, budget)
                continue

            if state["stage"] == "terminated":
                self._grade(spec, task, paths, state)
                continue

            if state["stage"] == "graded":
                self._write_ledger(spec, paths, state, budget)
                continue

            raise LiveEpisodeError(f"unsupported episode stage: {state['stage']}")
        return self.summary(spec, paths, state, budget)

    def _invoke(self, spec: LiveEpisodeSpec, task: dict, paths: dict[str, Path],
                action: dict, history: list[dict]) -> dict:
        if action["kind"] == "worker":
            policy = json.loads((POLICY_DIR / f"{spec.policy_id}.json").read_text(encoding="utf-8"))
            guidance = f"\nController guidance:\n{action['guidance']}" if action.get("guidance") else ""
            observations = [self._controller_observation(row) for row in history]
            prior = ("\nPrior observable attempts:\n"
                     + json.dumps(observations, sort_keys=True, ensure_ascii=False)) if observations else ""
            request = evaluation_live_worker.WorkerRequest(
                actor_root=paths["actor"],
                issue=(realworld.FIXTURES / task["issue"]).read_text(encoding="utf-8"),
                allowed_edits=tuple(task["allowed_edits"]),
                requested_cell=action["requested_cell"],
                allowance_usd=action["allowance_usd"],
                policy="\n".join(policy["rules"]) + prior + guidance,
            )
            return self.worker.run(request)
        request = evaluation_live_controller.ControllerRequest(
            actor_root=paths["actor"], controller_root=paths["controllers"],
            allowance_usd=action["allowance_usd"], invocation_id=action["invocation_id"],
            issue=(realworld.FIXTURES / task["issue"]).read_text(encoding="utf-8"),
            allowed_edits=tuple(task["allowed_edits"]),
            observations=tuple(self._controller_observation(row) for row in history),
        )
        return self.controller.run(request)  # type: ignore[union-attr]

    @staticmethod
    def _controller_observation(row: dict) -> dict:
        return {key: row.get(key) for key in (
            "kind", "requested_cell", "public_passed", "public_returncode",
            "public_output_tail", "boundary_ok", "boundary_changes",
            "actor_digest", "controller_outcome", "cross_module_conflict",
        )}

    def _reconcile_action(self, spec: LiveEpisodeSpec, task: dict, paths: dict[str, Path],
                          state: dict, budget: DispatchBudget) -> None:
        action = state["current_action"]
        outcome = state["pending_outcome"]
        invocation_id = action["invocation_id"]
        terminal = outcome.get("terminal") is True
        cost = outcome.get("cost_usd")
        budget.settle(invocation_id, cost if isinstance(cost, (int, float)) else None,
                      final=terminal and isinstance(cost, (int, float)),
                      telemetry={"status": outcome.get("status"),
                                 "usage": outcome.get("usage"),
                                 "actual_model": outcome.get("actual_model")},
                      evidence="adapter-terminal-envelope" if terminal and cost is not None
                      else "adapter-incomplete-envelope")
        history = {
            "sequence": action["sequence"], "kind": action["kind"],
            "requested_cell": action["requested_cell"], "reason": action["reason"],
            "invocation_id": invocation_id, "allowance_usd": action["allowance_usd"],
            "terminal": terminal, "status": outcome.get("status", "failed"),
            "actual_model": outcome.get("actual_model"),
            "identity_valid": outcome.get("identity_valid"),
            "effort_evidence": outcome.get("effort_evidence"),
            "usage": outcome.get("usage") or evaluation_runner.UNKNOWN_USAGE,
            "cost_usd": cost, "started_at": outcome.get("started_at"),
            "finished_at": outcome.get("finished_at"),
            "wall_clock_s": outcome.get("wall_clock_s"),
            "actor_digest": state["pending_actor_snapshot"]["digest"],
            "served_models": outcome.get("served_models"),
            "billed_models": outcome.get("billed_models"),
            "auxiliary_billed_models": outcome.get("auxiliary_billed_models"),
        }
        if action["kind"] == "worker":
            public = realworld.run_checks(paths["actor"], paths["actor"] / "public_checks", False)
            boundary_ok, boundary_changes = realworld.edit_boundary(
                task, state["baseline"], paths["actor"])
            history.update(public_passed=public["passed"] and boundary_ok,
                           public_returncode=public["returncode"],
                           public_output_tail=public["output_tail"], boundary_ok=boundary_ok,
                           boundary_changes=boundary_changes,
                           cross_module_conflict=outcome.get("cross_module_conflict") is True)
        else:
            controller_outcome = outcome.get("controller_outcome")
            if controller_outcome not in {"solution", "gap", "dissolved", "error"}:
                raise LiveEpisodeError(f"invalid Controller outcome: {controller_outcome!r}")
            history.update(controller_outcome=controller_outcome,
                           guidance=outcome.get("guidance"),
                           controller_run_dir=outcome.get("controller_run_dir"),
                           winning_technique=outcome.get("winning_technique"),
                           inner_accounting=outcome.get("inner_accounting"))
        state["history"].append(history)
        state.pop("current_action", None)
        state.pop("pending_outcome", None)
        state.pop("pending_actor_snapshot", None)
        if not terminal or cost is None:
            state["stop_reason"] = "incomplete_provider_accounting"
            self._save(paths, state, "blocked", "action_accounting_uncertain", {
                "invocation_id": invocation_id, "allowance_retained": True,
            })
        elif action["kind"] == "worker" and outcome.get("identity_valid") is not True:
            state["stop_reason"] = "worker_identity_mismatch"
            self._save(paths, state, "blocked", "worker_identity_rejected", {
                "invocation_id": invocation_id, "actual_model": outcome.get("actual_model"),
            })
        elif action["kind"] == "controller" and outcome.get("identity_valid") is not True:
            state["stop_reason"] = "controller_identity_mismatch"
            self._save(paths, state, "blocked", "controller_identity_rejected", {
                "invocation_id": invocation_id,
                "served_models": outcome.get("served_models"),
            })
        else:
            self._save(paths, state, "ready", "action_reconciled", {
                "invocation_id": invocation_id, "cost_usd": cost,
                "public_passed": history.get("public_passed"),
            })

    def _grade(self, spec: LiveEpisodeSpec, task: dict, paths: dict[str, Path], state: dict) -> None:
        before = realworld.protected_hashes(task)
        hidden = realworld.run_checks(paths["actor"], realworld.ORACLES / spec.task_id, True)
        boundary_ok, boundary_changes = realworld.edit_boundary(
            task, state["baseline"], paths["actor"])
        after = realworld.protected_hashes(task)
        grade = {
            "status": "pass" if hidden["passed"] and boundary_ok else "fail",
            "accepted": hidden["passed"] and boundary_ok,
            "hidden_returncode": hidden["returncode"], "boundary_ok": boundary_ok,
            "boundary_changes": boundary_changes, "oracle_unchanged": before == after,
        }
        state["grade"] = grade
        self._save(paths, state, "graded", "external_grade_recorded", grade)

    def _write_ledger(self, spec: LiveEpisodeSpec, paths: dict[str, Path], state: dict,
                      budget: DispatchBudget) -> None:
        attempts = []
        for row in state["history"]:
            passed = row.get("public_passed") is True
            attempts.append({
                "id": f"att-{row['sequence']:03d}", "sequence": row["sequence"],
                "invocation_id": row["invocation_id"],
                "parent_invocation_id": None if row["sequence"] == 1
                else state["history"][row["sequence"] - 2]["invocation_id"],
                "start_kind": "direct" if row["sequence"] == 1 else "escalation",
                "requested_cell": row["requested_cell"], "actual_model": row.get("actual_model"),
                "effort_evidence": row.get("effort_evidence"),
                "bundle_version": state["manifest"]["bundle_version"],
                "policy_version": state["manifest"]["policy_sha256"],
                "started_at": row.get("started_at") or LOGICAL_TIME,
                "finished_at": row.get("finished_at") or LOGICAL_TIME,
                "execution_status": row["status"],
                "outcome": "pass" if passed else "fail",
                "wall_clock_s": row.get("wall_clock_s"),
                "usage": row["usage"],
            })
        grade = state["grade"]
        acceptance_record = evaluation_runner.make_acceptance(paths, grade, spec.task_id)
        total_cost = sum(row["cost_usd"] for row in state["history"]
                         if isinstance(row.get("cost_usd"), (int, float)))
        total_wall = sum(row["wall_clock_s"] for row in state["history"]
                         if isinstance(row.get("wall_clock_s"), (int, float)))
        controller_rows = [row for row in state["history"] if row["kind"] == "controller"]
        controller_run_dir = next((row.get("controller_run_dir") for row in reversed(controller_rows)
                                   if row.get("controller_run_dir")), None)
        winning_technique = next((row.get("winning_technique") for row in reversed(controller_rows)
                                  if row.get("winning_technique")), None)
        record = {
            "type": "RoutingLedgerEntry", "id": "led-001", "ledger_version": 2,
            "references": [], "ts": LOGICAL_TIME, "task_slug": spec.task_id.lower(),
            "bucket": f"{spec.sensitivity}/{spec.horizon}/{spec.blast}",
            "self_directed": spec.self_directed,
            "first_cell": attempts[0]["requested_cell"],
            "escalations": [{"cell": row["requested_cell"], "outcome": row["outcome"]}
                            for row in attempts[1:]],
            "final_outcome": "pass" if grade["accepted"] else "fail",
            "cost_usd": round(total_cost, 9), "wall_clock_s": round(total_wall, 6),
            "controller_run_dir": controller_run_dir,
            "winning_technique": winning_technique,
            "notes": f"live evaluation policy {spec.policy_id}",
            "context": {"peak_tokens": None, "window": None,
                        "compactions": None, "source": "none"},
            "execution_status": "completed" if grade["accepted"] else "failed",
            "attempts": attempts, "acceptance": acceptance_record,
        }
        errors = validate_records.validate_record(record, validate_records.load_schemas())
        if errors:
            raise LiveEpisodeError(f"invalid routing record: {errors}")
        paths["ledger"].write_text(json.dumps(record, sort_keys=True) + "\n",
                                   encoding="utf-8", newline="\n")
        state["ledger_sha256"] = file_sha256(paths["ledger"])
        state["budget"] = evaluation_runner.normalise_budget(budget.snapshot())
        state["learning_eligible"] = bool(
            acceptance.qualified(record["acceptance"])
            and all(row.get("identity_valid") is True for row in state["history"])
            and not budget.snapshot()["unresolved"]
        )
        self._save(paths, state, "complete", "episode_completed", {
            "ledger_sha256": state["ledger_sha256"],
            "learning_eligible": state["learning_eligible"],
        })

    def summary(self, spec: LiveEpisodeSpec | None, paths: dict[str, Path],
                state: dict, budget: DispatchBudget) -> dict:
        event_ok, event_detail = evaluation_runner.validate_events(paths["events"])
        snapshot = evaluation_runner.normalise_budget(budget.snapshot())
        invocations = snapshot.get("invocations", {})
        retained = sum(max(0, row["allowance_units"] - row["charged_units"])
                       for row in invocations.values() if row["state"] != "settled") / 1_000_000_000
        return {
            "episode_id": paths["base"].name,
            "policy_id": spec.policy_id if spec else state["manifest"]["policy_id"],
            "stage": state["stage"], "stop_reason": state.get("stop_reason"),
            "sequence": [row["requested_cell"] for row in state.get("history", [])],
            "event_chain_valid": event_ok, "event_chain_detail": event_detail,
            "dispatch_events": sum(row["kind"] == "action_dispatched"
                                   for row in evaluation_runner.read_events(paths["events"])),
            "reserved_usd": retained, "grade": state.get("grade"),
            "learning_eligible": state.get("learning_eligible", False),
            "ledger_sha256": state.get("ledger_sha256"),
        }


def known_usage(cost: float, includes_descendants: bool = False) -> dict:
    return {
        "input_tokens": 100, "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0, "output_tokens": 20,
        "cost_usd": cost, "currency": "USD", "cost_source": "provider_reported",
        "price_snapshot": "test/fixtures/realworld/price-snapshot-2026-09-17.json",
        "includes_descendants": includes_descendants,
    }


class ScriptedWorker:
    """Overlay scripted fixture variants without making model calls."""

    def __init__(self, variants: list[str | BaseException], cost_usd: float | None = 0.05):
        self.variants = list(variants)
        self.cost_usd = cost_usd
        self.calls: list[str] = []

    def run(self, request: evaluation_live_worker.WorkerRequest) -> dict:
        self.calls.append(request.requested_cell)
        step = self.variants.pop(0)
        if isinstance(step, BaseException):
            raise step
        realworld.overlay(realworld.FIXTURES / "development" / "D01" / "variants" / step,
                          request.actor_root)
        model, effort = evaluation_live_worker.cell_identity(request.requested_cell)
        terminal = self.cost_usd is not None
        return {
            "status": "completed" if terminal else "interrupted", "terminal": terminal,
            "cost_usd": self.cost_usd, "usage": known_usage(self.cost_usd)
            if self.cost_usd is not None else evaluation_runner.UNKNOWN_USAGE,
            "actual_model": model, "identity_valid": True,
            "effort_evidence": f"scripted:{effort}",
            "started_at": LOGICAL_TIME, "finished_at": LOGICAL_TIME, "wall_clock_s": 0.1,
        }


class ScriptedController:
    def __init__(self, outcomes: list[str]):
        self.outcomes = list(outcomes)
        self.calls = 0

    def run(self, request: evaluation_live_controller.ControllerRequest) -> dict:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        return {
            "status": "completed", "terminal": True, "cost_usd": 0.10,
            "usage": known_usage(0.10, includes_descendants=True),
            "actual_model": "controller-multi-role", "identity_valid": True,
            "effort_evidence": "scripted-controller", "controller_outcome": outcome,
            "guidance": "Preserve explicit falsey values by testing against None.",
            "controller_run_dir": f"{request.invocation_id}/runs/controller",
            "winning_technique": "subtract", "served_models": ["claude-sonnet-5"],
            "billed_models": ["claude-sonnet-5"], "auxiliary_billed_models": [],
            "inner_accounting": {"complete": True, "known_spend_usd": 0.10,
                                 "reserved_usd": 0.0, "unresolved": [], "calls": 1},
            "started_at": LOGICAL_TIME, "finished_at": LOGICAL_TIME, "wall_clock_s": 0.2,
        }


def run_qualification(work: Path) -> dict:
    cases: dict[str, dict] = {}

    def run_case(name: str, policy: str, variants: list[str], controller=None) -> tuple[dict, ScriptedWorker]:
        worker = ScriptedWorker(variants)
        runner = LiveEpisodeRunner(work / name, worker, controller)
        result = runner.run(LiveEpisodeSpec(name, "D01", policy))
        cases[name] = result
        return result, worker

    b0, b0_worker = run_case("b0-repair", "B0", ["wrong_contract", "reference"])
    b1, b1_worker = run_case("b1-ladder", "B1", ["wrong_contract", "alternative"])
    b2_controller = ScriptedController(["solution"])
    b2, b2_worker = run_case("b2-controller", "B2",
                             ["wrong_happy", "wrong_contract", "reference"], b2_controller)
    b2_ledger = json.loads(
        (work / "b2-controller" / "b2-controller" / "routing-ledger.jsonl")
        .read_text(encoding="utf-8")
    )

    crash_worker = ScriptedWorker([RuntimeError("synthetic crash after dispatch")])
    crash_spec = LiveEpisodeSpec("crash-recovery", "D01", "B0")
    crash_root = work / "crash"
    crashed = False
    try:
        LiveEpisodeRunner(crash_root, crash_worker).run(crash_spec)
    except RuntimeError as exc:
        crashed = str(exc) == "synthetic crash after dispatch"
    resume_worker = ScriptedWorker(["reference"])
    recovered = LiveEpisodeRunner(crash_root, resume_worker).run(crash_spec)
    cases["crash_recovery"] = recovered

    missing_worker = ScriptedWorker(["reference"], cost_usd=None)
    missing = LiveEpisodeRunner(work / "missing", missing_worker).run(
        LiveEpisodeSpec("missing-cost", "D01", "B0"))
    cases["missing_cost"] = missing

    checks = {
        "b0_repairs_once_at_floor": b0["stage"] == "complete"
        and b0_worker.calls == ["worker-sonnet-low", "worker-sonnet-low"]
        and b0["grade"]["accepted"] is True,
        "b1_uses_frozen_ladder": b1["stage"] == "complete"
        and b1_worker.calls == ["worker-sonnet-low", "worker-opus-high"]
        and b1["grade"]["accepted"] is True,
        "b2_requires_two_distinct_failures": b2["stage"] == "complete"
        and b2["sequence"] == ["worker-sonnet-low", "worker-sonnet-low", "controller",
                              "worker-sonnet-low"]
        and b2_controller.calls == 1 and b2["grade"]["accepted"] is True,
        "dispatch_recovery_never_redispatches": crashed and recovered["stage"] == "blocked"
        and recovered["dispatch_events"] == 1 and resume_worker.calls == []
        and recovered["reserved_usd"] > 0,
        "missing_cost_retains_allowance": missing["stage"] == "blocked"
        and missing["stop_reason"] == "incomplete_provider_accounting"
        and missing["reserved_usd"] > 0 and missing["grade"] is None,
        "event_chains_valid": all(case["event_chain_valid"] for case in cases.values()),
        "hidden_grade_after_policy_stop": all(
            case["grade"] is not None for case in (b0, b1, b2)
        ),
        "controller_metadata_reaches_routing_ledger":
        b2_ledger["controller_run_dir"] == "inv-b2-controller-003/runs/controller"
        and b2_ledger["winning_technique"] == "subtract",
        "policy_boundary_excludes_forbidden_inputs": set(
            PolicyExecutor.decide.__annotations__
        ).isdisjoint({"task_id", "source_project_name", "hidden_grade", "reference_solution"}),
    }
    return {
        "schema_version": 1, "mode": "offline-scripted-adapters-v1",
        "offline_only": True, "model_calls": 0,
        "result": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "cases": cases,
        "limits": [
            "Scripted adapters qualify policy ordering, external grading and recovery without model calls.",
            "The live worker adapter is separately calibrated and qualified.",
            "The live Controller adapter is qualified separately with injected provider-free accounting.",
        ],
    }


def render_report(value: dict) -> str:
    lines = [
        "# Live episode integration offline qualification", "",
        f"Result: **{value['result']}**. Mode: `{value['mode']}`. Model calls: **0**.", "",
        "| Check | Result |", "| :--- | :--- |",
    ]
    lines.extend(f"| {name.replace('_', ' ')} | {'pass' if passed else 'fail'} |"
                 for name, passed in value["checks"].items())
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in value["limits"])
    return "\n".join(lines) + "\n"


def validate(path: Path) -> tuple[bool, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read live episode evidence: {exc}"
    recorded = value.pop("evidence_sha256", None)
    report = value.get("report") or {}
    report_path = (ROOT / str(report.get("path", ""))).resolve()
    checks = value.get("checks") or {}
    ok = bool(
        recorded == digest(value) and value.get("result") == "PASS"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == file_sha256(Path(__file__))
        and len(checks) == 9 and all(checks.values())
        and report_path.is_relative_to(ROOT.resolve()) and report_path.is_file()
        and report.get("sha256") == file_sha256(report_path)
    )
    return ok, f"mode={value.get('mode')}; digest={'valid' if recorded == digest(value) else 'invalid'}"


def atomic_json(path: Path, value: dict) -> None:
    evaluation_runner.atomic_json(path, value)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = args.report if args.report.is_absolute() else ROOT / args.report
    if args.check:
        ok, detail = validate(output)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    with tempfile.TemporaryDirectory(prefix="live-episode-qualification-") as folder:
        value = run_qualification(Path(folder))
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(value), encoding="utf-8", newline="\n")
    value.update({
        "implementation_sha256": file_sha256(Path(__file__)),
        "report": {"path": report.relative_to(ROOT).as_posix(), "sha256": file_sha256(report)},
    })
    value["evidence_sha256"] = digest(value)
    atomic_json(output, value)
    print(f"{value['result']}: wrote {output.relative_to(ROOT)} and {report.relative_to(ROOT)}")
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
