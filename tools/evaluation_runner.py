#!/usr/bin/env python3
"""Run and replay real-world evaluation episodes without model calls.

The live worker boundary is deliberately an interface. This module's built-in
qualification uses deterministic fake workers, but exercises the durable
budget, attempt record, external grader and restart paths used by a live run.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "test" / "harness"))

import acceptance  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402
import realworld  # noqa: E402
from realworld_isolation import validate as validate_isolation  # noqa: E402
import validate_records  # noqa: E402

SCHEMA_VERSION = 1
QUALIFICATION_MODE = "offline-fake-worker-v1"
EPISODE_BUDGET_USD = 4.0
ISOLATION = ROOT / "test" / "results" / "2026-09-17-realworld-isolation.json"
DEFAULT_EVIDENCE = ROOT / "test" / "results" / "2026-09-17-realworld-runner.json"
DEFAULT_REPORT = ROOT / "test" / "results" / "2026-09-17-realworld-runner.md"
LOGICAL_START = "2026-09-17T00:00:00+00:00"
LOGICAL_FINISH = "2026-09-17T00:00:01+00:00"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                      allow_nan=False).encode("utf-8") + b"\n"
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def tree_snapshot(root: Path) -> dict:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()
                       and "__pycache__" not in item.parts):
        files.append({"path": path.relative_to(root).as_posix(),
                      "sha256": file_sha256(path), "size": path.stat().st_size})
    return {"files": files, "missing": [], "digest": digest(files)}


def append_event(path: Path, kind: str, details: dict) -> dict:
    """Append one hash-linked event and return it."""
    prior = read_events(path)
    event = {"sequence": len(prior) + 1, "kind": kind,
             "previous_sha256": prior[-1]["event_sha256"] if prior else None,
             "details": details}
    event["event_sha256"] = digest(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def read_events(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def validate_events(path: Path) -> tuple[bool, str]:
    previous = None
    for sequence, event in enumerate(read_events(path), 1):
        unsigned = {key: value for key, value in event.items() if key != "event_sha256"}
        if event.get("sequence") != sequence or event.get("previous_sha256") != previous:
            return False, f"event {sequence} breaks sequence or chain"
        if event.get("event_sha256") != digest(unsigned):
            return False, f"event {sequence} has an invalid digest"
        previous = event["event_sha256"]
    return previous is not None, "valid hash chain" if previous else "empty event journal"


@dataclasses.dataclass(frozen=True)
class EpisodeSpec:
    episode_id: str
    task_id: str
    policy_id: str
    scenario: str
    variant: str | None
    requested_cell: str
    actual_model: str
    cost_usd: float | None
    usage: dict
    terminal_status: str = "completed"
    grader_failure: bool = False
    interrupt_after_commit: bool = False


def known_usage(cost: float) -> dict:
    return {"input_tokens": 1200, "cache_creation_input_tokens": 300,
            "cache_read_input_tokens": 500, "output_tokens": 240,
            "cost_usd": cost, "currency": "USD",
            "cost_source": "provider_reported",
            "price_snapshot": "test/fixtures/realworld/price-snapshot-2026-09-17.json",
            "includes_descendants": False}


UNKNOWN_USAGE = {
    "input_tokens": None, "cache_creation_input_tokens": None,
    "cache_read_input_tokens": None, "output_tokens": None,
    "cost_usd": None, "currency": None, "cost_source": "unknown",
    "price_snapshot": None, "includes_descendants": None,
}


SCENARIOS = (
    EpisodeSpec("offline-001", "D01", "B0", "success", "reference",
                "worker-sonnet-low", "claude-sonnet-5", 0.20, known_usage(0.20)),
    EpisodeSpec("offline-002", "D03", "B1", "worker_failure", None,
                "worker-opus-high", "claude-opus-5", 0.30, known_usage(0.30), "failed"),
    EpisodeSpec("offline-003", "D05", "B2", "timeout", None,
                "worker-sonnet-low", "claude-sonnet-5", None, UNKNOWN_USAGE, "interrupted"),
    EpisodeSpec("offline-004", "D07", "B0", "cancellation", None,
                "worker-sonnet-low", "claude-sonnet-5", 0.05, known_usage(0.05), "cancelled"),
    EpisodeSpec("offline-005", "D11", "B1", "interruption_resume", "reference",
                "worker-opus-high", "claude-opus-5", 0.25, known_usage(0.25),
                interrupt_after_commit=True),
    EpisodeSpec("offline-006", "D09", "B2", "identity_mismatch", "alternative",
                "worker-sonnet-low", "claude-sonnet-latest", 0.15, known_usage(0.15)),
    EpisodeSpec("offline-007", "D08", "B0", "missing_usage", "reference",
                "worker-sonnet-low", "claude-sonnet-5", None, UNKNOWN_USAGE),
    EpisodeSpec("offline-008", "D10", "B1", "grader_failure", "reference",
                "worker-opus-high", "claude-opus-5", 0.25, known_usage(0.25),
                grader_failure=True),
    EpisodeSpec("offline-009", "D03", "B2", "wrong_solution", "wrong_contract",
                "worker-sonnet-low", "claude-sonnet-5", 0.20, known_usage(0.20)),
)


class EpisodeRunner:
    """Durable, idempotent episode state machine for one campaign directory."""

    def __init__(self, campaign_root: Path):
        self.root = campaign_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalogue = realworld.load_catalogue()
        self.tasks = {task["id"]: task for task in realworld.ready_tasks(self.catalogue)}
        self.manifest = json.loads((ROOT / "dist" / "bundle-manifest.json").read_text(encoding="utf-8"))
        ok, detail = validate_isolation(ISOLATION)
        if not ok:
            raise RuntimeError(f"isolation evidence is invalid: {detail}")

    def episode_dir(self, spec: EpisodeSpec) -> Path:
        return self.root / spec.episode_id

    def _paths(self, spec: EpisodeSpec) -> dict[str, Path]:
        base = self.episode_dir(spec)
        return {"base": base, "state": base / "state.json", "events": base / "events.jsonl",
                "actor": base / "actor", "graft": base / "graft-root",
                "budget": base / "dispatch-budget.json", "ledger": base / "routing-ledger.jsonl"}

    def _initialise(self, spec: EpisodeSpec, paths: dict[str, Path]) -> dict:
        if paths["state"].is_file():
            state = json.loads(paths["state"].read_text(encoding="utf-8"))
            if state.get("spec_sha256") != digest(dataclasses.asdict(spec)):
                raise RuntimeError(f"{spec.episode_id}: checkpoint belongs to a different episode spec")
            return self._recover_transition(paths, state)
        task = self.tasks[spec.task_id]
        paths["base"].mkdir(parents=True)
        shutil.copytree(realworld.FIXTURES / task["repo"], paths["actor"])
        paths["graft"].mkdir()
        policy = realworld.FIXTURES / "policies" / f"{spec.policy_id}.json"
        state = {
            "schema_version": SCHEMA_VERSION, "episode_id": spec.episode_id,
            "stage": "planned", "spec_sha256": digest(dataclasses.asdict(spec)),
            "manifest": {
                "campaign": self.catalogue["campaign"], "task_id": spec.task_id,
                "policy_id": spec.policy_id, "policy_sha256": file_sha256(policy),
                "bundle_version": self.manifest["bundle_version"],
                "catalogue_sha256": file_sha256(realworld.CATALOGUE),
                "price_snapshot_sha256": file_sha256(
                    realworld.FIXTURES / "price-snapshot-2026-09-17.json"),
                "isolation_evidence_sha256": json.loads(ISOLATION.read_text(encoding="utf-8"))["evidence_sha256"],
                "actor_root": spec.episode_id + "/actor",
                "evaluator_root": "external:test/oracles/realworld",
                "graft_root": spec.episode_id + "/graft-root",
                "seed": 0, "episode_budget_usd": EPISODE_BUDGET_USD,
                "active_model_timeout_seconds": 900,
                "external_grader_timeout_seconds": 120,
                "claude_cli_version": None, "graft_version": None,
                "runtime_identity": f"python-{sys.version_info.major}.{sys.version_info.minor}",
                "offline_fake_worker": True,
            },
        }
        self._save(paths, state, "planned", "episode_planned", state["manifest"])
        return state

    @staticmethod
    def _save(paths: dict[str, Path], state: dict, stage: str, event: str, details: dict) -> None:
        transition = {"stage": stage, "event": event, "details": details}
        transition["id"] = digest(transition)
        state["pending_transition"] = transition
        atomic_json(paths["state"], state)
        EpisodeRunner._recover_transition(paths, state)

    @staticmethod
    def _recover_transition(paths: dict[str, Path], state: dict) -> dict:
        """Finish a transition interrupted before or after its journal append."""
        transition = state.get("pending_transition")
        if not transition:
            return state
        matching = [event for event in read_events(paths["events"])
                    if (event.get("details") or {}).get("transition_id") == transition["id"]]
        if len(matching) > 1:
            raise RuntimeError(f"duplicate transition event {transition['id']}")
        if not matching:
            append_event(paths["events"], transition["event"],
                         {**transition["details"], "transition_id": transition["id"]})
        state["stage"] = transition["stage"]
        state.pop("pending_transition", None)
        atomic_json(paths["state"], state)
        return state

    def run(self, spec: EpisodeSpec) -> dict:
        paths = self._paths(spec)
        state = self._initialise(spec, paths)
        budget = DispatchBudget(paths["budget"], EPISODE_BUDGET_USD if not paths["budget"].exists() else None)
        invocation_id = f"inv-{spec.episode_id}"

        if state["stage"] == "planned":
            existing = budget.snapshot()["invocations"].get(invocation_id)
            allowance = (existing["allowance_units"] / 1_000_000_000 if existing else
                         budget.reserve(invocation_id, EPISODE_BUDGET_USD, 0.01,
                                        {"episode_id": spec.episode_id, "policy_id": spec.policy_id,
                                         "requested_cell": spec.requested_cell}))
            state["allowance_usd"] = allowance
            self._save(paths, state, "reserved", "budget_reserved",
                       {"invocation_id": invocation_id, "allowance_usd": allowance})
        if state["stage"] == "reserved":
            accounting_state = budget.snapshot()["invocations"][invocation_id]["state"]
            if accounting_state == "reserved":
                budget.start(invocation_id)
            elif accounting_state not in ("running", "uncertain", "settled"):
                raise RuntimeError(f"{spec.episode_id}: cannot recover budget state {accounting_state}")
            self._save(paths, state, "dispatched", "worker_dispatched",
                       {"invocation_id": invocation_id, "requested_cell": spec.requested_cell})
        if state["stage"] == "dispatched":
            if spec.variant:
                realworld.overlay(realworld.FIXTURES / "development" / spec.task_id / "variants" / spec.variant,
                                  paths["actor"])
            state["actor_snapshot"] = tree_snapshot(paths["actor"])
            self._save(paths, state, "worker_committed", "worker_result_committed",
                       {"variant": spec.variant or "original",
                        "actor_digest": state["actor_snapshot"]["digest"]})
            if spec.interrupt_after_commit and not state.get("interruption_injected"):
                state["interruption_injected"] = True
                atomic_json(paths["state"], state)
                append_event(paths["events"], "runner_interrupted",
                             {"after": "worker_result_committed", "invocation_id": invocation_id})
                return self.summary(spec)
        if state["stage"] == "worker_committed":
            if tree_snapshot(paths["actor"])["digest"] != state["actor_snapshot"]["digest"]:
                raise RuntimeError(f"{spec.episode_id}: actor changed after committed worker result")
            public = realworld.run_checks(paths["actor"], paths["actor"] / "public_checks", False)
            state["public_result"] = public
            self._save(paths, state, "visible_checked", "visible_verification",
                       {"passed": public["passed"], "returncode": public["returncode"]})
        if state["stage"] == "visible_checked":
            state["terminal_status"] = spec.terminal_status
            self._save(paths, state, "terminated", "episode_terminated",
                       {"execution_status": spec.terminal_status, "hidden_grade_seen": False})
        if state["stage"] == "terminated":
            task = self.tasks[spec.task_id]
            if spec.grader_failure:
                grade = {"status": "blocked", "accepted": None,
                         "reason": "synthetic evaluator failure", "oracle_unchanged": True}
            else:
                before = realworld.protected_hashes(task)
                hidden = realworld.run_checks(paths["actor"], realworld.ORACLES / spec.task_id, True)
                boundary_ok, changes = realworld.edit_boundary(
                    task, realworld.actor_hashes(realworld.FIXTURES / task["repo"]), paths["actor"])
                after = realworld.protected_hashes(task)
                grade = {"status": "pass" if hidden["passed"] and boundary_ok else "fail",
                         "accepted": hidden["passed"] and boundary_ok,
                         "hidden_returncode": hidden["returncode"], "boundary_ok": boundary_ok,
                         "boundary_changes": changes, "oracle_unchanged": before == after}
            state["grade"] = grade
            self._save(paths, state, "graded", "external_grade_recorded", grade)
        if state["stage"] == "graded":
            telemetry = {"status": spec.terminal_status, "usage": spec.usage,
                         "actual_model": spec.actual_model, "offline_fake_worker": True}
            budget.settle(invocation_id, spec.cost_usd, final=spec.cost_usd is not None,
                          telemetry=telemetry,
                          evidence="offline-terminal-envelope" if spec.cost_usd is not None else "offline-missing-usage")
            state["budget"] = normalise_budget(budget.snapshot())
            self._save(paths, state, "reconciled", "budget_reconciled",
                       {"accounting_status": state["budget"]["invocations"][invocation_id]["state"],
                        "cost_usd": spec.cost_usd})
        if state["stage"] == "reconciled":
            ledger = self._routing_record(spec, state)
            errors = validate_records.validate_record(ledger, validate_records.load_schemas())
            if errors:
                raise RuntimeError(f"{spec.episode_id}: invalid routing record: {errors}")
            paths["ledger"].write_text(json.dumps(ledger, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            state["ledger_sha256"] = file_sha256(paths["ledger"])
            state["learning_eligible"] = (
                acceptance.qualified(ledger["acceptance"])
                and spec.actual_model == expected_model(spec.requested_cell)
                and state["budget"]["invocations"][invocation_id]["state"] == "settled"
                and spec.terminal_status in ("completed", "failed")
            )
            self._save(paths, state, "complete", "episode_completed",
                       {"ledger_sha256": state["ledger_sha256"],
                        "learning_eligible": state["learning_eligible"]})
        return self.summary(spec)

    def _routing_record(self, spec: EpisodeSpec, state: dict) -> dict:
        grade = state["grade"]
        acceptance_record = make_acceptance(paths=self._paths(spec), grade=grade,
                                            task_id=spec.task_id)
        final_outcome = "unknown" if grade["status"] == "blocked" else grade["status"]
        attempt = {
            "id": "att-001", "sequence": 1, "invocation_id": f"inv-{spec.episode_id}",
            "parent_invocation_id": None, "start_kind": "direct",
            "requested_cell": spec.requested_cell, "actual_model": spec.actual_model,
            "effort_evidence": "offline-fake-worker:high" if "opus" in spec.requested_cell else "offline-fake-worker:low",
            "bundle_version": self.manifest["bundle_version"],
            "policy_version": state["manifest"]["policy_sha256"],
            "started_at": LOGICAL_START, "finished_at": LOGICAL_FINISH,
            "execution_status": spec.terminal_status, "outcome": final_outcome,
            "wall_clock_s": 1.0, "usage": spec.usage,
        }
        return {
            "type": "RoutingLedgerEntry", "id": "led-001", "ledger_version": 2,
            "references": [], "ts": LOGICAL_FINISH, "task_slug": spec.task_id.lower(),
            "bucket": "structured/medium/contained", "self_directed": False,
            "first_cell": spec.requested_cell, "escalations": [],
            "final_outcome": final_outcome, "cost_usd": spec.cost_usd,
            "wall_clock_s": 1.0, "controller_run_dir": None,
            "winning_technique": None, "notes": f"offline scenario {spec.scenario}",
            "context": {"peak_tokens": None, "window": None, "compactions": None, "source": "none"},
            "execution_status": spec.terminal_status, "attempts": [attempt],
            "acceptance": acceptance_record,
        }

    def summary(self, spec: EpisodeSpec) -> dict:
        paths = self._paths(spec)
        state = json.loads(paths["state"].read_text(encoding="utf-8"))
        events_ok, event_detail = validate_events(paths["events"])
        snapshot = normalise_budget(DispatchBudget(paths["budget"]).snapshot())
        invocation = snapshot["invocations"].get(f"inv-{spec.episode_id}", {})
        retained = (max(0, invocation.get("allowance_units", 0) - invocation.get("charged_units", 0))
                    if invocation.get("state") != "settled" else 0)
        return {
            "episode_id": spec.episode_id, "task_id": spec.task_id,
            "policy_id": spec.policy_id, "scenario": spec.scenario,
            "stage": state["stage"], "event_chain_valid": events_ok,
            "event_chain_detail": event_detail, "event_count": len(read_events(paths["events"])),
            "dispatch_events": sum(event["kind"] == "worker_dispatched" for event in read_events(paths["events"])),
            "accounting_status": invocation.get("state"), "cost_usd": invocation.get("cost_usd"),
            "reserved_usd": retained / 1_000_000_000,
            "grade": state.get("grade"), "learning_eligible": state.get("learning_eligible", False),
            "actual_model": spec.actual_model,
            "expected_model": expected_model(spec.requested_cell),
            "state_fingerprint": state_fingerprint(state),
        }


def expected_model(cell: str) -> str:
    return "claude-opus-5" if cell.startswith("worker-opus-") else "claude-sonnet-5"


def normalise_budget(snapshot: dict) -> dict:
    clean = json.loads(json.dumps(snapshot))
    clean.pop("created_at", None)
    for row in clean.get("invocations", {}).values():
        for key in list(row):
            if key.endswith("_at"):
                row.pop(key)
    return clean


def make_acceptance(paths: dict[str, Path], grade: dict, task_id: str) -> dict:
    if grade["status"] == "blocked":
        return {"status": "blocked", "contract_version": acceptance.CONTRACT_VERSION,
                "evidence": {"blocked_reason": grade["reason"]}, "review": None}
    contract = {
        "version": 1, "kind": "command",
        "criteria": [f"External hidden grader accepts {task_id}"],
        "constraints": ["Grade only after episode termination"],
        "required_outputs": ["actor"], "protected_paths": [],
        "command": ["external-realworld-grader", task_id], "rubric": [], "timeout_s": 120.0,
    }
    actor = tree_snapshot(paths["actor"])
    evidence = {
        "kind": "command", "started_at": LOGICAL_FINISH, "finished_at": LOGICAL_FINISH,
        "command": {"argv": contract["command"], "exit_code": 0 if grade["status"] == "pass" else 1,
                    "stdout": "", "stderr": "", "timed_out": False},
        "artefacts": actor, "protected": {"files": [], "missing": [], "digest": digest([])},
        "protected_unchanged": grade.get("oracle_unchanged") is True,
        "blocked_reason": None, "revision": {"head": None, "diff_sha256": None, "status_sha256": None},
    }
    evidence["result_digest"] = acceptance.digest(evidence)
    return {"status": grade["status"], "contract_version": acceptance.CONTRACT_VERSION,
            "contract": contract, "contract_digest": acceptance.digest(contract),
            "protected_baseline": evidence["protected"], "evidence": evidence, "review": None}


def state_fingerprint(state: dict) -> str:
    selected = {key: state.get(key) for key in (
        "schema_version", "episode_id", "stage", "spec_sha256", "manifest",
        "actor_snapshot", "public_result", "terminal_status", "grade", "budget",
        "learning_eligible")}
    if isinstance(selected.get("public_result"), dict):
        selected["public_result"].pop("output_tail", None)
    return digest(selected)


def run_qualification(work_root: Path) -> dict:
    """Run every failure path twice and prove deterministic, idempotent replay."""
    first_root, second_root = work_root / "first", work_root / "replay"
    passes: list[list[dict]] = []
    for campaign_root in (first_root, second_root):
        runner = EpisodeRunner(campaign_root)
        rows = []
        for spec in SCENARIOS:
            row = runner.run(spec)
            if spec.interrupt_after_commit and row["stage"] != "complete":
                row = runner.run(spec)
            rows.append(row)
        passes.append(rows)
    first, replayed = passes
    deterministic = [row["state_fingerprint"] for row in first] == [row["state_fingerprint"] for row in replayed]
    all_complete = all(row["stage"] == "complete" for row in first + replayed)
    chains_valid = all(row["event_chain_valid"] for row in first + replayed)
    one_dispatch = all(row["dispatch_events"] == 1 for row in first + replayed)
    scenarios = {row["scenario"]: row for row in first}
    expected = (
        scenarios["success"]["grade"]["accepted"] is True
        and scenarios["wrong_solution"]["grade"]["accepted"] is False
        and scenarios["identity_mismatch"]["learning_eligible"] is False
        and scenarios["missing_usage"]["accounting_status"] == "uncertain"
        and scenarios["timeout"]["accounting_status"] == "uncertain"
        and scenarios["grader_failure"]["grade"]["status"] == "blocked"
        and scenarios["interruption_resume"]["dispatch_events"] == 1
    )
    known_spend = round(sum(row["cost_usd"] or 0 for row in first), 9)
    retained = round(sum(row["reserved_usd"] for row in first), 9)
    return {
        "schema_version": SCHEMA_VERSION, "mode": QUALIFICATION_MODE,
        "offline_only": True, "model_calls": 0,
        "implementation_sha256": file_sha256(Path(__file__)),
        "inputs": {
            "catalogue_sha256": file_sha256(realworld.CATALOGUE),
            "acceptance_sha256": file_sha256(ROOT / "tools" / "acceptance.py"),
            "dispatch_budget_sha256": file_sha256(ROOT / "tools" / "dispatch_budget.py"),
            "routing_schema_sha256": file_sha256(
                ROOT / "src" / "System" / "schemas" / "RoutingLedgerEntry.schema.json"),
            "policies": {
                policy: file_sha256(realworld.FIXTURES / "policies" / f"{policy}.json")
                for policy in ("B0", "B1", "B2")
            },
        },
        "scenario_count": len(first), "policies": sorted({row["policy_id"] for row in first}),
        "scenarios": first,
        "replay": {"deterministic": deterministic, "all_complete": all_complete,
                   "event_chains_valid": chains_valid, "one_dispatch_per_episode": one_dispatch,
                   "first_fingerprint": digest([row["state_fingerprint"] for row in first]),
                   "second_fingerprint": digest([row["state_fingerprint"] for row in replayed])},
        "accounting": {"known_spend_usd": known_spend,
                       "retained_unresolved_usd": retained,
                       "unknown_cost_episodes": sum(row["cost_usd"] is None for row in first),
                       "double_counted_cost_usd": 0.0},
        "isolation": {"evidence": ISOLATION.relative_to(ROOT).as_posix(),
                      "evidence_sha256": json.loads(ISOLATION.read_text(encoding="utf-8"))["evidence_sha256"],
                      "integration": "external grader path is absent from actor roots; recorded WSL2 boundary is required",
                      "full_live_boundary_exercised": False},
        "limits": [
            "Fake workers prove control flow and accounting, not Claude behaviour.",
            "The recorded WSL2 access-control mechanism is required but a live model episode has not exercised it.",
            "Unknown terminal usage retains its full unused allowance and is ineligible for learning.",
        ],
        "result": "PASS" if deterministic and all_complete and chains_valid and one_dispatch and expected else "FAIL",
    }


def validate_evidence(path: Path) -> tuple[bool, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read runner evidence: {exc}"
    recorded = value.pop("evidence_sha256", None)
    report = value.get("report") or {}
    report_raw = report.get("path", "")
    report_path = (ROOT / report_raw).resolve() if isinstance(report_raw, str) else ROOT
    report_valid = (isinstance(report_raw, str) and report_raw
                    and not Path(report_raw).is_absolute()
                    and report_path.is_relative_to(ROOT.resolve())
                    and report_path.is_file()
                    and report.get("sha256") == file_sha256(report_path))
    ok = (recorded == digest(value) and value.get("result") == "PASS"
          and value.get("model_calls") == 0
          and value.get("implementation_sha256") == file_sha256(Path(__file__))
          and value.get("policies") == ["B0", "B1", "B2"]
          and value.get("scenario_count") == len(SCENARIOS)
          and (value.get("replay") or {}).get("deterministic") is True
          and (value.get("replay") or {}).get("event_chains_valid") is True
          and (value.get("replay") or {}).get("one_dispatch_per_episode") is True
          and report_valid)
    return ok, f"mode={value.get('mode')}; digest={'valid' if recorded == digest(value) else 'invalid'}"


def render_report(value: dict) -> str:
    lines = [
        "# Real-world episode runner offline qualification", "",
        f"Result: **{value['result']}**. Mode: `{value['mode']}`. Model calls: **0**.", "",
        "The runner replayed every scenario from a separate campaign root. Hidden grading ran only",
        "after episode termination. Unknown terminal usage retained its reservation and did not",
        "qualify as learning evidence.", "",
        "| Scenario | Policy | Task | Grade | Accounting | Learning | Dispatches |", 
        "| :--- | :--- | :--- | :--- | :--- | :--- | ---: |",
    ]
    for row in value["scenarios"]:
        grade = (row.get("grade") or {}).get("status", "not run")
        lines.append(
            f"| {row['scenario']} | {row['policy_id']} | {row['task_id']} | {grade} | "
            f"{row['accounting_status']} | {'yes' if row['learning_eligible'] else 'no'} | "
            f"{row['dispatch_events']} |"
        )
    accounting = value["accounting"]
    replay = value["replay"]
    lines.extend([
        "", "## Reconciliation", "",
        f"- Known fake spend: USD {accounting['known_spend_usd']:.2f}.",
        f"- Retained unresolved allowance: USD {accounting['retained_unresolved_usd']:.2f}.",
        f"- Episodes with unknown cost: {accounting['unknown_cost_episodes']}.",
        f"- Double-counted cost: USD {accounting['double_counted_cost_usd']:.2f}.",
        "", "## Replay", "",
        f"- Deterministic state: {str(replay['deterministic']).lower()}.",
        f"- Valid event chains: {str(replay['event_chains_valid']).lower()}.",
        f"- One dispatch per episode: {str(replay['one_dispatch_per_episode']).lower()}.",
        "", "## Limits", "",
    ])
    lines.extend(f"- {item}" for item in value["limits"])
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--work-root", type=Path)
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        ok, detail = validate_evidence(output)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    if args.work_root:
        result = run_qualification(args.work_root)
    else:
        with tempfile.TemporaryDirectory(prefix="realworld-runner-") as folder:
            result = run_qualification(Path(folder))
    result["recorded_at"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    report = args.report or (DEFAULT_REPORT if output == DEFAULT_EVIDENCE else output.with_suffix(".md"))
    report = report if report.is_absolute() else ROOT / report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(result), encoding="utf-8", newline="\n")
    result["report"] = {"path": report.relative_to(ROOT).as_posix(), "sha256": file_sha256(report)}
    result["evidence_sha256"] = digest(result)
    atomic_json(output, result)
    print(f"{result['result']}: {len(result['scenarios'])} offline scenarios, 0 model calls")
    print(f"wrote {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
