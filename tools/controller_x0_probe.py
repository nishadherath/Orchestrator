#!/usr/bin/env python3
"""Offline characterisations of the pre-remediation Controller boundaries.

This records defects, not a qualification pass. All dispatches use explicit
fakes; temporary manifests bind current bytes without rewriting paid history.
X1-X4 can reuse individual probes and require the unsafe observations to cease.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

import acceptance
import controller_control as controls
import controller_corpus as corpus
import controller_dispatch as dispatch
import controller_evaluation as evaluation
import controller_campaign_manifest as campaign_manifest
import controller_integrity as integrity
import controller_matrix_runtime as matrix
import controller_pilot_runtime as pilot
import controller_policy as policy
from dispatch_budget import DispatchBudget
import model_registry
import system_controller as controller

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    """Write only to the caller's explicit output or disposable fixture tree."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)
                    + "\n", encoding="utf-8", newline="\n")


def fresh_manifest(kind: str) -> dict:
    """Make a current-code offline fixture using the historical schedule only."""
    contract = evaluation.load_contract()
    if kind == "matrix-calibration":
        episodes = evaluation.matrix_episodes(contract, model_registry.load())
        maximum = 48.75
    elif kind == "instrumented-pilot":
        episodes = evaluation.pilot_episodes(contract)
        maximum = 144.0
    else:
        raise ValueError(f"unsupported offline campaign kind: {kind!r}")
    value = campaign_manifest.upgrade(evaluation._manifest(kind, episodes, maximum), ROOT)
    value.update(execution_enabled=True, launch_readiness="authorisation-required")
    value["manifest_sha256"] = evaluation.digest(
        {k: v for k, v in value.items() if k != "manifest_sha256"})
    return value


def manifest_files(root: Path, manifest: dict) -> tuple[Path, Path]:
    manifest_path, auth_path = root / "manifest.json", root / "offline-auth.json"
    write_json(manifest_path, manifest)
    write_json(auth_path, {"schema_version": 1, "decision": "approved",
                          "manifest_sha256": manifest["manifest_sha256"],
                          "maximum_authorised_usd": manifest["maximum_authorised_usd"],
                          "approved_at": "offline-fixture", "approved_by": "offline-probe"})
    return manifest_path, auth_path


def terminal_restart(root: Path) -> dict:
    """A settled failed result differs from an interrupted in-flight call."""
    results = {}
    for name, runtime, kind in (("matrix", matrix, "matrix-calibration"),
                                ("pilot", pilot, "instrumented-pilot")):
        calls = []

        class SettledFailure:
            def run(self, *args):
                episode = args[0] if name == "matrix" else args[1]
                calls.append(episode["sequence"])
                return {"status": "failed", "terminal": True,
                        "cost_usd": .01, "identity_valid": True,
                        "accounting_complete": True}

        manifest, auth = manifest_files(root / name, fresh_manifest(kind))
        first = runtime.execute(manifest, auth, root / name / "run", SettledFailure())
        first_calls = len(calls)
        second = runtime.execute(manifest, auth, root / name / "run", SettledFailure())
        results[name] = {"first_status": first["status"], "second_status": second["status"],
                         "sequences": calls, "additional_calls": len(calls) - first_calls,
                         "known_spend_usd": second["known_spend_usd"]}
    return results


def dependency_binding(root: Path) -> dict:
    """Mutate disposable copies, including one bound-file rejection control."""
    unbound = ("tools/dispatch_budget.py", "tools/system_controller.py",
               "tools/claudep.py", "tools/system_prompts.py", "tools/acceptance.py",
               "tools/evaluation_live_worker.py", "tools/evaluation_runner.py",
               "tools/controller_evaluation.py", "src/System/ROLES.md")
    results = {}
    for name, runtime, kind in (("matrix", matrix, "matrix-calibration"),
                                ("pilot", pilot, "instrumented-pilot")):
        value = fresh_manifest(kind)
        clone = root / name
        for relative in set(value["bound_files"]) | set(unbound):
            path = clone / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        admitted = []
        with patch.object(runtime, "ROOT", clone):
            runtime.validate_manifest(value)
            for relative in unbound:
                path = clone / relative
                original = path.read_bytes()
                suffix = (b'\nraise RuntimeError("X0 changed executable dependency")\n'
                          if path.suffix == ".py" else b"\nX0 changed role contract\n")
                path.write_bytes(original + suffix)
                try:
                    runtime.validate_manifest(value)
                    admitted.append(relative)
                except (matrix.MatrixRuntimeError, pilot.PilotRuntimeError):
                    pass
                finally:
                    path.write_bytes(original)
            bound = next(iter(value["bound_files"]))
            path = clone / bound
            path.write_bytes(path.read_bytes() + b"\n")
            try:
                runtime.validate_manifest(value)
                bound_rejected = False
            except (matrix.MatrixRuntimeError, pilot.PilotRuntimeError):
                bound_rejected = True
        results[name] = {"changed_unbound_files_admitted": admitted,
                         "bound_file_change_rejected": bound_rejected,
                         "bound_file_count": len(value["bound_files"])}
    return results


def public_label_credit(root: Path) -> dict:
    """Build a counterfeit using only the materialised C01-D1 public fields."""
    task = next(row for row in corpus.load_corpus()["tasks"] if row["task_id"] == "C01-D1")
    actor = root / "actor"
    corpus.materialise(task, actor)
    public = json.loads((actor / "task.json").read_text(encoding="utf-8"))
    observations = json.loads((actor / "observations.json").read_text(encoding="utf-8"))
    before = {p.name: evaluation.file_digest(p) for p in actor.iterdir()}
    answer = {"semantic_outcome": "accepted-full",
              "action": "repair-" + public["mechanism_label"],
              "diagnosis": public["mechanism_label"],
              "completed_milestones": public["objective_milestones"],
              "evidence_ids": [row["id"] for row in observations],
              "remaining_blocker": "none", "next_step": "run-public-and-hidden-acceptance",
              "completion_claim": "complete", "mutations": []}
    write_json(actor / "result.json", answer)
    grade = corpus.grade_task(task, answer)
    return {"task_id": task["task_id"], "grade": grade,
            "all_original_files_unchanged": all(evaluation.file_digest(actor / p) == h
                                                for p, h in before.items()),
            "only_new_file": sorted(p.name for p in actor.iterdir() if p.name not in before),
            "candidate_input": "materialised public fields only; no oracle or variant reads"}


def assessment_bias(root: Path) -> dict:
    """Hold actor/problem constant while changing the private family label."""
    root.mkdir(parents=True)
    (root / "input.txt").write_text("unchanged public evidence\n", encoding="utf-8")
    revision = acceptance.revision(root)
    problem = "Inspect the supplied evidence and determine the next action."
    records = {}
    for family in ("C01", "N01"):
        assessment = pilot._assessment({"family_id": family}, root, problem, revision)
        control = controls.ControlDecision("auto", "shipped-default", 0,
                                            assessment["task_revision"], "x0")
        decision = policy.decide(assessment, control)
        records[family] = {"assessment": assessment, "action": decision["effective_action"]}
    return {"same_actor_problem_and_revision": True, "family_results": records}


class NoCalls:
    def run(self, request):
        raise AssertionError("this probe must not invoke a worker or Controller")


def canned_clarification(root: Path) -> dict:
    task = next(row for row in corpus.load_corpus()["tasks"] if row["task_id"] == "N03-D1")
    episode = {"arm": "A", "selected_cell": "worker-sonnet-low",
               "controller_profile": "standard", "maximum_usd": 8.0}
    result = pilot.PilotEpisodeExecutor(NoCalls(), NoCalls()).run(task, episode, root)
    return {"grade": result["grade"], "worker_attempts": len(result["worker_attempts"]),
            "controller_used": result["controller_used"], "cost_usd": result["cost_usd"]}


def generator_dispatch(root: Path) -> dict:
    root.mkdir(parents=True)
    budget = DispatchBudget(root / "budget.json", 4.0)
    runner = controller.LiveRoleRunner(root, budget.remaining, budget=budget,
                                       role_profile="frontier-candidate")
    calls = []

    def fake_call(prompt, **kwargs):
        calls.append({"prompt": prompt, "model": kwargs["model"], "effort": kwargs["effort"]})
        return SimpleNamespace(cost_usd=.01, result="{}", elapsed_s=0.0,
                               extras={}, raw={"type": "result"})

    with patch.object(controller.claudep, "call_claude", side_effect=fake_call):
        caps = runner.generator_plan(list(controller.TECHNIQUE_FAMILIES))
        for family in controller.TECHNIQUE_FAMILIES:
            runner("generate", "generator", f"Independent evidence context for {family}",
                   timeout=1, technique=family, call_cap_usd=caps[family])
    configured = model_registry.resolve_role_profile("frontier-candidate")["roles"]["generator"]
    return {"configured_cells": [row["name"] for row in configured], "dispatches": calls,
            "distinct_dispatched_cells": sorted({f"worker-{r['model']}-{r['effort']}" for r in calls}),
            "known_spend_usd": budget.snapshot()["spent_usd"]}


def task_inputs(root: Path) -> tuple[str, dict, dict, dict]:
    root.mkdir(parents=True)
    (root / "input.txt").write_text("stable public input\n", encoding="utf-8")
    problem = "Inspect the consequential premise conflict."
    revision = acceptance.revision(root)
    family = evaluation.load_contract()["families"][0]
    assessment, _ = evaluation._assessment(family, 0)
    assessment["task_revision"] = policy.derive_task_revision(problem, root, revision)
    contract = {"criteria": ["independent acceptance"], "constraints": ["preserve inputs"]}
    return problem, revision, assessment, {"contract": contract,
                                           "contract_digest": integrity.digest(contract)}


def settled_gap(cost: float) -> dict:
    return {"terminal": True, "accounting_complete": True, "cost_usd": cost,
            "outcome": "gap", "evidence_packet": None, "controller_run_dir": None}


def competing_admissions(root: Path) -> dict:
    problem, revision, assessment, acceptance_state = task_inputs(root)
    decisions = []
    for mode in ("auto", "on"):
        control = controls.ControlDecision(mode, "explicit", 1, assessment["task_revision"], "x0")
        decisions.append(policy.decide(assessment, control))
    barrier = threading.Barrier(2, timeout=10)
    calls = []

    class Capture:
        def run(self, request):
            calls.append({"invocation_id": request.invocation_id,
                          "task_revision": request.task_revision,
                          "allowance_usd": request.allowance_usd})
            barrier.wait()
            return settled_gap(.01)

    adapter = Capture()
    def invoke(decision):
        return dispatch.TaskDispatcher(root, adapter).dispatch(
            decision, problem_text=problem, input_revision=revision,
            acceptance_state=acceptance_state)

    with ThreadPoolExecutor(max_workers=2) as pool:
        states = list(pool.map(invoke, decisions))
    count = len(calls)
    replay = invoke(decisions[0])
    return {"distinct_decisions": len({r["decision_id"] for r in decisions}),
            "distinct_task_revisions": len({r["task_revision"] for r in decisions}),
            "adapter_calls": calls, "stages": [r["stage"] for r in states],
            "same_decision_replay_calls": len(calls) - count, "replay_stage": replay["stage"]}


def failed_cost_projection(root: Path) -> dict:
    task = next(row for row in corpus.load_corpus()["tasks"] if row["task_id"] == "C01-D1")
    class CostlyGap:
        def run(self, request):
            return settled_gap(.25)

    episode = {"arm": "A", "selected_cell": "worker-sonnet-low",
               "controller_profile": "standard", "maximum_usd": 8.0}
    result = pilot.PilotEpisodeExecutor(NoCalls(), CostlyGap()).run(task, episode, root)
    budgets = list((root / "actor/.claude/controller-dispatch").glob("*/task-budget.json"))
    snapshot = DispatchBudget(budgets[0], scope="task_dispatch").snapshot()
    return {"episode_cost_usd": result["cost_usd"],
            "episode_accounting_complete": result["accounting_complete"],
            "durable_known_spend_usd": snapshot["spent_usd"],
            "durable_unresolved": snapshot["unresolved"]}


def run_probes() -> dict:
    probes = {"terminal_restart": terminal_restart, "dependency_binding": dependency_binding,
              "public_label_credit": public_label_credit, "assessment_bias": assessment_bias,
              "canned_clarification": canned_clarification, "generator_dispatch": generator_dispatch,
              "competing_admissions": competing_admissions, "failed_cost_projection": failed_cost_projection}
    with tempfile.TemporaryDirectory(prefix="controller-x0-") as raw:
        observations = {name: probe(Path(raw) / name) for name, probe in probes.items()}
    sources = ["tools/controller_x0_probe.py", "tools/controller_evaluation.py",
               "tools/controller_matrix_runtime.py", "tools/controller_pilot_runtime.py",
               "tools/controller_corpus.py", "tools/controller_dispatch.py",
               "tools/system_controller.py", "tools/controller_policy.py", "src/model_registry.json"]
    return {"schema_version": 1, "stage": "X0", "provider_calls": 0,
            "result": "CHARACTERISED_NOT_QUALIFIED", "observations": observations,
            "source_sha256": {p: evaluation.file_digest(ROOT / p) for p in sources}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_probes()
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
