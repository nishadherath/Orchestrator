#!/usr/bin/env python3
"""Provider-free paired X3 plumbing through the production workflow.

The fake worker gives both arms the same final quality. These checks establish
admission, accounting and handoff comparability, not Controller uplift.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_control  # noqa: E402
import controller_dispatch  # noqa: E402
import controller_policy  # noqa: E402
import controller_public_assessment  # noqa: E402
import controller_workflow  # noqa: E402
import model_registry  # noqa: E402
import task_executor  # noqa: E402
import worker_selector  # noqa: E402
from test.harness.controller_routing_r4_tests import FakeAdapter as FakeController  # noqa: E402

FIXTURES = ROOT / "test" / "fixtures" / "controller_x3" / "development"


class FakeWorker:
    """Apply an authored reference at the worker adapter boundary only."""

    offline_fake = True

    def __init__(self, variant: Path):
        self.variant = variant
        self.calls = []

    def capability(self, actor_root: Path) -> dict:
        return {"actor_root": str(actor_root.resolve()),
                "enforcement_proven": False, "budget_enforced": True,
                "supported_cells": sorted(model_registry.load()["cells"])}

    def run(self, request) -> dict:
        self.calls.append(request)
        for source in self.variant.rglob("*"):
            if source.is_file():
                target = request.actor_root / source.relative_to(self.variant)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        cell = model_registry.resolve_cell(request.requested_cell)
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": cell["expected_provider_model"],
                "identity_valid": True, "child_models": [],
                "status": "completed", "terminal": True,
                "writer_stopped": True, "cost_usd": .1,
                "usage": {"cost_usd": .1, "cost_source": "synthetic-fixture",
                          "currency": "USD", "input_tokens": 0,
                          "output_tokens": 0, "cache_creation_input_tokens": 0,
                          "cache_read_input_tokens": 0},
                "effort_evidence": f"cli-argument:{cell['effort']}",
                "started_at": "2026-09-28T00:00:00Z",
                "finished_at": "2026-09-28T00:00:01Z", "wall_clock_s": 1.0}


def interpret_public(packet: dict) -> dict:
    """Tiny deterministic interpreter double over public bytes, never labels."""
    issue = next(row["content"] for row in packet["sources"]
                 if row["path"] == packet["issue_path"])
    consequential = ("idempotency key" in issue and "charging again" in issue)
    worker = {"task_kind": "implementation",
              "complexity": "complex" if consequential else "routine",
              "verification": "executable", "failure_cause": "none",
              "frame_confidence": "clear"}
    rigour = {"consequence": "consequential" if consequential else "contained",
              "premise_uncertainty": "specific-checkable" if consequential else "none",
              "alternatives": "several-material" if consequential else "one-established",
              "constraint_coupling": "cross-module" if consequential else "local",
              "verification_gap": "incomplete-checks" if consequential
                                  else "strong-existing-checks",
              "observed_failure_cause": "none", "required_output": "patch",
              "evidence_availability": "available"}
    fields = worker | rigour
    return {"interpretation": {"schema_version": 1, "classifications": fields,
                               "field_evidence": {key: ["e1", "e2"] for key in fields},
                               "material_evidence": ["e1"] if consequential else []},
            "telemetry": {"provider_calls": 0, "model": None, "cost_usd": 0,
                          "input_tokens": 0, "output_tokens": 0}}


def prepare(project: Path, task_id: str,
            experimental_dispatch: dict | None = None) -> tuple[task_executor.TaskExecutor, str, FakeWorker]:
    fixture = FIXTURES / task_id
    shutil.copytree(fixture / "actor", project)
    editable = json.loads((project / "acceptance.json").read_text(
        encoding="utf-8"))["editable_paths"]
    contract = project / "n1-acceptance.json"
    contract.write_text(json.dumps({
        "version": 1, "kind": "command", "criteria": ["public check passes"],
        "constraints": [], "required_outputs": editable,
        "protected_paths": ["issue.md", "app.py", "public_check.py"],
        "command": [sys.executable, "-B", "public_check.py"], "timeout_s": 10,
    }), encoding="utf-8")
    worker = FakeWorker(fixture / "variants" / "reference")
    executor = task_executor.TaskExecutor(project, worker)
    goal = (project / "issue.md").read_text(encoding="utf-8")
    root = executor.admit(goal=goal, scope=editable, permissions=["read", "edit"],
                          input_paths=["issue.md", "app.py", "public_check.py"],
                          acceptance_path=contract, budget_usd=12.0,
                          authority_id="offline-pair-grant", actor="offline-pair",
                          root_id="offline-pair-root",
                          experimental_dispatch=experimental_dispatch)
    return executor, root, worker


def assess_and_decide(executor: task_executor.TaskExecutor, root: str,
                      worker: FakeWorker, mode: str) -> tuple[dict, dict, dict]:
    project = executor.project
    record = executor.status(root)
    editable = record["definition"]["scope"]
    source = next(path for path in editable if path != "report.json")
    sources = list(dict.fromkeys(["issue.md", "app.py", "public_check.py", source]))
    heading = next(line for line in (project / "issue.md").read_text(
        encoding="utf-8").splitlines() if line.startswith("# "))
    public_lines = (project / "public_check.py").read_text(
        encoding="utf-8").splitlines()
    assertion = next(line for line in public_lines
                     if line.lstrip().startswith("assert ")
                     and public_lines.count(line) == 1)
    assessment = controller_public_assessment.assess_with(
        project, issue="issue.md", source_paths=sources,
        quote_requests=[{"source": "issue.md", "quote": heading},
                        {"source": "public_check.py", "quote": assertion}],
        input_revision=record["definition"]["input_revision"],
        interpreter=interpret_public,
        operational={"context_tokens": 1000, "deadline_seconds": None,
                     "prior_local_repairs": 0, "required_artefacts": editable,
                     "deadline": None, "authorised_task_budget_usd": 12.0,
                     "observed_at": "2026-09-28T00:00:00Z"})
    shadow = worker_selector.select(
        assessment["worker"],
        supported_cells=set(worker.capability(project)["supported_cells"]),
        remaining_usd=12.0, budget_enforced=True)
    control = controller_control.ControlDecision(
        mode, "explicit" if mode == "off" else "shipped-default", 0,
        assessment["rigour"]["task_revision"], "offline-pair")
    decision = controller_policy.decide(
        assessment["rigour"], control,
        selected_cell=record["ladder"][0])
    return assessment, shadow, decision


class PairedPathTests(unittest.TestCase):
    def test_common_production_workflow_charges_assessment_in_both_arms(self):
        """S and A use the same public interpreter and N1 accounting path."""
        with tempfile.TemporaryDirectory(prefix="x3-common-workflow-") as raw:
            for task_id, expected_actions in (
                    ("N04-D1", {"S": "worker", "A": "worker"}),
                    ("C03-D1", {"S": "worker", "A": "controller"})):
                observations = {}
                public_packets = {}
                for arm, mode in (("S", "off"), ("A", "auto")):
                    executor, root, worker = prepare(Path(raw) / task_id / arm,
                                                     task_id)
                    record = executor.status(root)
                    editable = record["definition"]["scope"]
                    source = next(path for path in editable if path != "report.json")
                    heading = next(line for line in (executor.project / "issue.md")
                                   .read_text(encoding="utf-8").splitlines()
                                   if line.startswith("# "))
                    public_lines = (executor.project / "public_check.py")\
                        .read_text(encoding="utf-8").splitlines()
                    assertion = next(line for line in public_lines
                                     if line.lstrip().startswith("assert ")
                                     and public_lines.count(line) == 1)

                    def interpreter(packet):
                        public_packets[arm] = packet
                        response = interpret_public(packet)
                        response["telemetry"] = {
                            "provider_calls": 1, "model": "claude-sonnet-5",
                            "cost_usd": .04, "input_tokens": 100,
                            "output_tokens": 20}
                        return response

                    result = controller_workflow.execute(
                        executor, root, issue="issue.md",
                        source_paths=list(dict.fromkeys([
                            "issue.md", "app.py", "public_check.py", source])),
                        quote_requests=[
                            {"source": "issue.md", "quote": heading},
                            {"source": "public_check.py", "quote": assertion}],
                        interpreter=interpreter,
                        operational={
                            "context_tokens": 1000, "deadline_seconds": None,
                            "prior_local_repairs": 0, "required_artefacts": editable,
                            "deadline": None, "authorised_task_budget_usd": 12.0,
                            "observed_at": "2026-09-28T00:00:00Z"},
                        assessment_allowance_usd=.5,
                        controller_adapter=FakeController(),
                        explicit_mode=mode)
                    self.assertEqual(expected_actions[arm],
                                     result["decision"]["effective_action"])
                    self.assertEqual("accepted", result["task"]["state"])
                    self.assertEqual("settled", result["task"]
                                     ["public_assessment"]["status"])
                    self.assertEqual(1, len(worker.calls))
                    self.assertEqual([], result["task"]["budget"]["unresolved"])
                    observations[arm] = result
                # Task revisions bind each arm's distinct project root. The
                # evidence visible to the assessor must still be identical.
                self.assertEqual(public_packets["S"]["sources"],
                                 public_packets["A"]["sources"])
                self.assertEqual(public_packets["S"]["citations"],
                                 public_packets["A"]["citations"])
                self.assertEqual(.14, observations["S"]["task"]
                                 ["budget"]["spent_usd"])
                self.assertEqual(.34 if task_id == "C03-D1" else .14,
                                 observations["A"]["task"]["budget"]["spent_usd"])

    def test_ordinary_pair_uses_same_public_and_n1_path(self):
        results = []
        with tempfile.TemporaryDirectory(prefix="x3-paired-ordinary-") as raw:
            for arm, mode in (("S", "off"), ("A", "auto")):
                executor, root, worker = prepare(Path(raw) / arm, "N04-D1")
                assessment, shadow, decision = assess_and_decide(
                    executor, root, worker, mode)
                self.assertEqual("worker", decision["effective_action"])
                self.assertEqual("shadow", shadow["mode"])
                dispatch = controller_dispatch.TaskDispatcher(
                    executor.project, FakeController(), root_task_id=root).dispatch(
                        decision, problem_text=executor.status(root)["definition"]["goal"],
                        acceptance_state={
                            "contract_digest": executor.status(root)["definition"]
                            ["acceptance_definition"]["contract_digest"]},
                        input_revision=executor.status(root)["definition"]["input_revision"])
                self.assertEqual("worker-ready", dispatch["stage"])
                result = executor.run(root)
                self.assertEqual("accepted", result["state"])
                self.assertEqual(1, len(worker.calls))
                results.append((assessment, shadow, decision, result))
        self.assertEqual(results[0][0]["worker"]["facts"],
                         results[1][0]["worker"]["facts"])
        self.assertEqual(results[0][1]["selected_cell"],
                         results[1][1]["selected_cell"])
        self.assertEqual([.1, .1], [row[3]["budget"]["spent_usd"] for row in results])

    def test_suitable_pair_exposes_x4_handoff_gate_without_false_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="x3-paired-suitable-") as raw:
            executor, root, worker = prepare(Path(raw) / "A", "C03-D1")
            assessment, shadow, decision = assess_and_decide(
                executor, root, worker, "auto")
            self.assertEqual("controller", decision["effective_action"])
            self.assertEqual("shadow", shadow["mode"])
            dispatch = controller_dispatch.TaskDispatcher(
                executor.project, FakeController(), root_task_id=root).dispatch(
                    decision, problem_text=executor.status(root)["definition"]["goal"],
                    acceptance_state={
                        "contract_digest": executor.status(root)["definition"]
                        ["acceptance_definition"]["contract_digest"]},
                    input_revision=executor.status(root)["definition"]["input_revision"])
            self.assertEqual("worker-ready", dispatch["stage"])
            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "resolve its handoff"):
                executor.run(root)
            self.assertEqual([], worker.calls)
            status = executor.status(root)
            self.assertEqual("ready", status["state"])
            self.assertEqual(.2, status["budget"]["spent_usd"])
            self.assertEqual([status["controller_admission"]
                              ["follow_on_invocation_id"]], status["budget"]["unresolved"])

    def test_consequential_pair_reaches_independent_acceptance_in_both_arms(self):
        """The same public assessment and N1 worker path serve S and A.

        A fake reference worker deliberately gives both arms the same final
        quality. This proves accounting and handoff comparability, not uplift.
        """
        with tempfile.TemporaryDirectory(prefix="x3-paired-complete-") as raw:
            observations = {}
            for arm, mode in (("S", "off"), ("A", "auto")):
                executor, root, worker = prepare(Path(raw) / arm, "C03-D1")
                assessment, shadow, decision = assess_and_decide(
                    executor, root, worker, mode)
                self.assertEqual("shadow", shadow["mode"])
                if arm == "A":
                    self.assertEqual("controller", decision["effective_action"])
                    frozen = executor.status(root)["definition"]
                    dispatch = controller_dispatch.TaskDispatcher(
                        executor.project, FakeController(), root_task_id=root).dispatch(
                            decision, problem_text=frozen["goal"],
                            acceptance_state={"contract_digest": frozen[
                                "acceptance_definition"]["contract_digest"]},
                            input_revision=frozen["input_revision"])
                    self.assertEqual("worker-ready", dispatch["stage"])
                    executor.accept_controller_handoff(root, decision["decision_id"])
                else:
                    self.assertEqual("worker", decision["effective_action"])
                result = executor.run(root)
                self.assertEqual("accepted", result["state"])
                self.assertEqual(1, len(worker.calls))
                observations[arm] = (assessment, decision, result)
            self.assertEqual(observations["S"][0]["worker"]["facts"],
                             observations["A"][0]["worker"]["facts"])
            self.assertEqual(observations["S"][1]["selected_cell"],
                             observations["A"][1]["selected_cell"])
            self.assertEqual(.1, observations["S"][2]["budget"]["spent_usd"])
            self.assertEqual(.3, observations["A"][2]["budget"]["spent_usd"])


if __name__ == "__main__":
    unittest.main()
