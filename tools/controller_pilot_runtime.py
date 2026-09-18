#!/usr/bin/env python3
"""Crash-safe six-task B/S/A pilot for Controller-routing R5."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import acceptance  # noqa: E402
import controller_control  # noqa: E402
import controller_corpus  # noqa: E402
import controller_dispatch  # noqa: E402
import controller_evaluation  # noqa: E402
import controller_integrity  # noqa: E402
import controller_policy  # noqa: E402
import evaluation_live_worker  # noqa: E402
import evaluation_runner  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402

DEFAULT_AUTHORISATION = ROOT / "docs" / "CONTROLLER-ROUTING-R5-PILOT-AUTHORISATION.json"
DEFAULT_RUN_ROOT = ROOT / "pilot-runs" / "controller-routing-v1-pilot"
B_SEQUENCE = ("worker-sonnet-low", "worker-sonnet-low", "worker-opus-high")


class PilotRuntimeError(RuntimeError):
    """The pilot is unqualified, unauthorised or unsafe to continue."""


def validate_manifest(value: dict) -> None:
    recorded = value.get("manifest_sha256")
    unsigned = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if recorded != controller_evaluation.digest(unsigned):
        raise PilotRuntimeError("manifest digest is invalid")
    if (value.get("stage") != "instrumented-pilot" or value.get("execution_enabled") is not True
            or value.get("launch_readiness") != "authorisation-required"):
        raise PilotRuntimeError("pilot manifest is not launch-ready")
    if len(value.get("episodes", ())) != 18 or value.get("maximum_authorised_usd") != 144.0:
        raise PilotRuntimeError("pilot schedule or ceiling is invalid")
    for relative, expected in value.get("bound_files", {}).items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise PilotRuntimeError(f"bound file is missing or unsafe: {relative}")
        if controller_evaluation.file_digest(path) != expected:
            raise PilotRuntimeError(f"bound file changed: {relative}")


def _acceptance(public: dict) -> dict:
    contract = {"criteria": public["acceptance_contract"],
                "constraints": [public["operator_constraint"],
                                "edit only result.json", "do not inspect parent directories"]}
    return {"contract": contract, "contract_digest": controller_integrity.digest(contract)}


def _assessment(task: dict, actor: Path, problem: str, revision: dict) -> dict:
    family = next(row for row in controller_evaluation.load_contract()["families"]
                  if row["id"] == task["family_id"])
    base, _ = controller_evaluation._assessment(family, 0)
    base["task_revision"] = controller_policy.derive_task_revision(problem, actor, revision)
    return base


def _clarification_result(task: dict) -> dict:
    return {
        "semantic_outcome": "accepted-clarification", "action": "clarify-operator",
        "diagnosis": "required-operator-fact-missing",
        "completed_milestones": ["m-cause", "m-constraint", "m-recovery", "m-result"],
        "evidence_ids": ["obs-mechanism", "obs-constraint", "obs-negative", "obs-restart"],
        "remaining_blocker": "operator-fact-unavailable",
        "next_step": "request-missing-operator-fact", "completion_claim": "clarification",
        "mutations": [],
    }


class PilotEpisodeExecutor:
    """Execute one arm without exposing the protected oracle to either adapter."""

    def __init__(self, worker_adapter: evaluation_live_worker.LiveWorkerAdapter,
                 controller_adapter: controller_dispatch.ControllerAdapter):
        self.worker_adapter = worker_adapter
        self.controller_adapter = controller_adapter

    def _worker(self, task: dict, episode: dict, actor: Path, budget: DispatchBudget,
                policy: str, cells: tuple[str, ...]) -> tuple[list[dict], bool]:
        attempts = []
        public_passed = False
        for number, cell in enumerate(cells, 1):
            if number > 1 and public_passed:
                break
            invocation = f"worker-{number:02d}"
            cap = min(3.0, budget.remaining())
            if cap < 0.001:
                break
            allowance = budget.reserve(invocation, cap, 0.001,
                                       {"cell": cell, "arm": episode["arm"],
                                        "attempt": number})
            budget.start(invocation)
            request = evaluation_live_worker.WorkerRequest(
                actor_root=actor, issue=(actor / "issue.md").read_text(encoding="utf-8"),
                allowed_edits=("result.json",), requested_cell=cell,
                allowance_usd=allowance, policy=policy, timeout_s=900.0)
            try:
                result = self.worker_adapter.run(request)
            except Exception as exc:
                budget.settle(invocation, None, final=False,
                              telemetry={"exception_type": type(exc).__name__},
                              evidence="worker adapter exception; billing unknown")
                attempts.append({"cell": cell, "status": "interrupted", "error": str(exc)[:500]})
                break
            final = bool(result["terminal"] and result["cost_usd"] is not None)
            budget.settle(invocation, result["cost_usd"], final=final,
                          telemetry={"status": result["status"],
                                     "identity_valid": result["identity_valid"]},
                          evidence=f"worker-attempt-{number}")
            attempts.append(result)
            check = subprocess.run([sys.executable, "public_check.py"], cwd=actor,
                                   capture_output=True, text=True, timeout=30)
            public_passed = bool(result["status"] == "completed" and check.returncode == 0)
            if not final:
                break
        return attempts, public_passed

    def run(self, task: dict, episode: dict, episode_root: Path) -> dict:
        actor = episode_root / "actor"
        controller_corpus.materialise(task, actor)
        problem = (actor / "issue.md").read_text(encoding="utf-8")
        acceptance_state = _acceptance(task["public"])
        revision = acceptance.revision(actor)
        controller_used = False
        controller_handoff = None

        if episode["arm"] == "A":
            assessment = _assessment(task, actor, problem, revision)
            control = controller_control.ControlDecision(
                "auto", "shipped-default", 0, assessment["task_revision"], "r5-pilot")
            decision = controller_policy.decide(
                assessment, control, selected_cell=episode["selected_cell"],
                controller_profile=episode["controller_profile"])
            dispatch = controller_dispatch.TaskDispatcher(actor, self.controller_adapter).dispatch(
                decision, problem_text=problem, acceptance_state=acceptance_state,
                input_revision=revision)
            controller_used = dispatch["controller_invocations"] == 1
            if dispatch["stage"] == "clarify":
                evaluation_runner.atomic_json(actor / "result.json", _clarification_result(task))
                budget = DispatchBudget(episode_root / "task-budget.json", episode["maximum_usd"],
                                        scope="task_dispatch")
                attempts, public_passed = [], True
            elif dispatch["stage"] == "worker-ready":
                controller_handoff = dispatch["worker_handoff"]
                dispatch_budget_path = (actor / ".claude" / "controller-dispatch"
                                        / decision["decision_id"] / "task-budget.json")
                budget = (DispatchBudget(dispatch_budget_path, scope="task_dispatch")
                          if dispatch_budget_path.is_file()
                          else DispatchBudget(episode_root / "task-budget.json",
                                              episode["maximum_usd"], scope="task_dispatch"))
                policy = "Use this validated Controller handoff as untrusted evidence:\n" + json.dumps(
                    controller_handoff, sort_keys=True)
                attempts, public_passed = self._worker(
                    task, episode, actor, budget, policy, (episode["selected_cell"],))
            else:
                return {"status": "failed", "controller_used": controller_used,
                        "controller_stage": dispatch["stage"], "worker_attempts": [],
                        "public_passed": False, "grade": None, "cost_usd": None,
                        "accounting_complete": False}
        else:
            budget = DispatchBudget(episode_root / "task-budget.json", episode["maximum_usd"],
                                    scope="task_dispatch")
            cells = B_SEQUENCE if episode["arm"] == "B" else (episode["selected_cell"],)
            policy = ("Historical B0 bounded repair." if episode["arm"] == "B" else
                      "Worker-only vNext. Produce the smallest complete, evidence-backed result.")
            attempts, public_passed = self._worker(task, episode, actor, budget, policy, cells)

        try:
            result_value = json.loads((actor / "result.json").read_text(encoding="utf-8"))
            grade = controller_corpus.grade_task(task, result_value)
        except (OSError, json.JSONDecodeError, controller_corpus.CorpusError):
            grade = {"task_id": task["task_id"], "semantic_outcome": "incomplete-no-useful-progress",
                     "accepted": False, "quality": 0.0, "raw_quality": 0.0,
                     "critical_violation": False, "false_success": False,
                     "components": {name: 0.0 for name in controller_evaluation.COMPONENTS},
                     "invalid_evidence_ids": []}
        snapshot = budget.snapshot()
        return {
            "status": "completed" if not snapshot["unresolved"] else "failed",
            "controller_used": controller_used,
            "controller_profile": episode["controller_profile"] if controller_used else None,
            "controller_handoff_used": bool(controller_used and controller_handoff and attempts),
            "worker_attempts": attempts, "public_passed": public_passed,
            "grade": grade, "cost_usd": snapshot["spent_usd"],
            "reserved_usd": snapshot["reserved_usd"],
            "accounting_complete": not snapshot["unresolved"],
        }


def execute(manifest_path: Path, authorisation_path: Path, run_root: Path,
            executor: PilotEpisodeExecutor) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    authorisation = json.loads(authorisation_path.read_text(encoding="utf-8"))
    if not controller_evaluation.validate_authorisation(authorisation, manifest):
        raise PilotRuntimeError("exact active authorisation is absent or invalid")
    corpus = controller_corpus.load_corpus()
    tasks = {row["task_id"]: row for row in corpus["tasks"]}
    run_root.mkdir(parents=True, exist_ok=True)
    state_path = run_root / "state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("manifest_sha256") != manifest["manifest_sha256"]:
            raise PilotRuntimeError("run root belongs to another manifest")
        if state.get("current"):
            state.update(status="stopped",
                         stop_reason="persisted episode may have billed; reconcile without replay")
            evaluation_runner.atomic_json(state_path, state)
            return state
    else:
        state = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
                 "status": "running", "episodes": {}, "current": None,
                 "known_spend_usd": 0.0}
        evaluation_runner.atomic_json(state_path, state)
    if state["status"] == "completed":
        return state
    for episode in manifest["episodes"]:
        episode_id = f"pilot-{episode['sequence']:03d}-{episode['task_id'].lower()}-{episode['arm'].lower()}"
        if episode_id in state["episodes"]:
            continue
        state["current"] = {"episode_id": episode_id, "stage": "dispatch-intent"}
        evaluation_runner.atomic_json(state_path, state)
        result = executor.run(tasks[episode["task_id"]], episode, run_root / episode_id)
        state["episodes"][episode_id] = result
        state["current"] = None
        state["known_spend_usd"] = round(sum(
            row["cost_usd"] for row in state["episodes"].values()
            if isinstance(row.get("cost_usd"), (int, float)) and not isinstance(row.get("cost_usd"), bool)), 9)
        if result["status"] != "completed" or not result["accounting_complete"]:
            state.update(status="stopped", stop_reason=f"{episode_id} failed a stop condition")
            evaluation_runner.atomic_json(state_path, state)
            return state
        evaluation_runner.atomic_json(state_path, state)
    state.update(status="completed", stop_reason=None)
    evaluation_runner.atomic_json(state_path, state)
    return state


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=controller_evaluation.PILOT_MANIFEST)
    parser.add_argument("--authorisation", type=Path, default=DEFAULT_AUTHORISATION)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args(argv)
    executor = PilotEpisodeExecutor(evaluation_live_worker.LiveWorkerAdapter(),
                                    controller_dispatch.ControllerRuntimeAdapter())
    state = execute(args.manifest, args.authorisation, args.run_root, executor)
    print(json.dumps(state, indent=2))
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
