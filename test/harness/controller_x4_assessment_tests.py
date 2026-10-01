#!/usr/bin/env python3
"""Provider-free X4 assessment accounting on the same N1 task root."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test.harness.controller_x3_pair_tests import interpret_public, prepare

import controller_control
import controller_dispatch
import controller_policy
import controller_public_assessment
import task_executor
import worker_selector
from test.harness.controller_routing_r4_tests import FakeAdapter as FakeController


class AssessmentTests(unittest.TestCase):
    def inputs(self, executor: task_executor.TaskExecutor, root: str) -> dict:
        project = executor.project
        editable = executor.status(root)["definition"]["scope"]
        source = next(path for path in editable if path != "report.json")
        heading = next(line for line in (project / "issue.md").read_text(
            encoding="utf-8").splitlines() if line.startswith("# "))
        assertion = next(line for line in (project / "public_check.py").read_text(
            encoding="utf-8").splitlines() if line.lstrip().startswith("assert "))
        return {
            "issue": "issue.md",
            "source_paths": list(dict.fromkeys(
                ["issue.md", "app.py", "public_check.py", source])),
            "quote_requests": [{"source": "issue.md", "quote": heading},
                               {"source": "public_check.py", "quote": assertion}],
            "operational": {"context_tokens": 1000, "deadline_seconds": None,
                            "prior_local_repairs": 0,
                            "required_artefacts": editable, "deadline": None,
                            "authorised_task_budget_usd": 12.0,
                            "observed_at": "2026-09-28T00:00:00Z"},
            "maximum_usd": .5,
        }

    def test_paid_assessment_controller_and_worker_share_one_root_budget(self):
        with tempfile.TemporaryDirectory(prefix="x4-assessment-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")

            def interpreter(packet):
                response = interpret_public(packet)
                response["telemetry"] = {"provider_calls": 1,
                                         "model": "claude-sonnet-5", "cost_usd": .04,
                                         "input_tokens": 100, "output_tokens": 20}
                return response

            assessment = executor.assess_public(root, interpreter=interpreter,
                                                **self.inputs(executor, root))
            recorded = executor.status(root)
            self.assertEqual("settled", recorded["public_assessment"]["status"])
            self.assertEqual(.04, recorded["budget"]["spent_usd"])
            self.assertEqual([], recorded["budget"]["unresolved"])
            self.assertEqual(11.96, assessment["rigour"]["authorised_task_budget_usd"])
            with self.assertRaises(task_executor.ExecutorError):
                task_executor.TaskExecutor(executor.project, worker).assess_public(
                    root, interpreter=interpreter, **self.inputs(executor, root))
            self.assertEqual(.04, executor.status(root)["budget"]["spent_usd"])
            control = controller_control.ControlDecision(
                "auto", "shipped-default", 0,
                assessment["rigour"]["task_revision"], "offline-pair")
            decision = controller_policy.decide(
                assessment["rigour"], control,
                selected_cell=recorded["ladder"][0])
            frozen = recorded["definition"]
            state = controller_dispatch.TaskDispatcher(
                executor.project, FakeController(), root_task_id=root).dispatch(
                    decision, problem_text=frozen["goal"],
                    acceptance_state={"contract_digest": frozen[
                        "acceptance_definition"]["contract_digest"]},
                    input_revision=frozen["input_revision"])
            self.assertEqual("worker-ready", state["stage"])
            executor.accept_controller_handoff(root, decision["decision_id"])
            result = executor.run(root)
            self.assertEqual("accepted", result["state"])
            self.assertEqual(.34, result["budget"]["spent_usd"])
            self.assertEqual(1, len(worker.calls))

    def test_uncertain_assessment_keeps_root_and_budget_closed(self):
        with tempfile.TemporaryDirectory(prefix="x4-assessment-uncertain-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")

            def interrupted(_packet):
                raise RuntimeError("provider response was lost")

            with self.assertRaises(task_executor.ExecutorError):
                executor.assess_public(root, interpreter=interrupted,
                                       **self.inputs(executor, root))
            recorded = executor.status(root)
            self.assertEqual("blocked", recorded["state"])
            self.assertEqual("uncertain", recorded["public_assessment"]["status"])
            self.assertEqual([recorded["public_assessment"]["invocation_id"]],
                             recorded["budget"]["unresolved"])
            self.assertEqual([], worker.calls)

    def test_public_reconciliation_closes_charge_but_never_replays_root(self):
        with tempfile.TemporaryDirectory(prefix="x4-assessment-reconcile-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")

            def parser_failed(_packet):
                raise RuntimeError("CLI response lost")

            with self.assertRaises(task_executor.ExecutorError):
                executor.assess_public(root, interpreter=parser_failed,
                                       **self.inputs(executor, root))
            fields = {"actor": "operator", "reason": "local parser rejected before provider",
                      "cost_usd": 0.0, "evidence": "terminal-cli-log:abc",
                      "writers_stopped": True}
            with self.assertRaisesRegex(task_executor.ExecutorError, "stopped writers"):
                executor.reconcile_public_assessment(root, **{**fields,
                                                           "writers_stopped": False})
            settled = executor.reconcile_public_assessment(root, **fields)
            self.assertEqual("blocked", settled["state"])
            self.assertEqual("invalid", settled["public_assessment"]["status"])
            self.assertEqual([], settled["budget"]["unresolved"])
            self.assertEqual(0, settled["budget"]["spent_usd"])
            self.assertEqual(settled, executor.reconcile_public_assessment(root, **fields))
            with self.assertRaisesRegex(task_executor.ExecutorError, "conflicts"):
                executor.reconcile_public_assessment(root, **{**fields,
                                                           "cost_usd": .01})
            with self.assertRaises(task_executor.ExecutorError):
                executor.assess_public(root, interpreter=parser_failed,
                                       **self.inputs(executor, root))
            self.assertEqual([], worker.calls)

    def test_invalid_interpretation_preserves_terminal_charge(self):
        with tempfile.TemporaryDirectory(prefix="x4-assessment-invalid-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")

            def invalid(packet):
                response = interpret_public(packet)
                response["interpretation"]["classifications"]["task_kind"] = "unsupported"
                response["telemetry"] = {"provider_calls": 1,
                                         "model": "claude-sonnet-5", "cost_usd": .04,
                                         "input_tokens": 100, "output_tokens": 20}
                return response

            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "public assessment failed closed"):
                executor.assess_public(root, interpreter=invalid,
                                       **self.inputs(executor, root))
            recorded = executor.status(root)
            self.assertEqual("blocked", recorded["state"])
            self.assertEqual("invalid", recorded["public_assessment"]["status"])
            self.assertEqual(.04, recorded["budget"]["spent_usd"])
            self.assertEqual([], recorded["budget"]["unresolved"])
            self.assertEqual([], worker.calls)

    def test_interpreter_failure_records_partial_charge_without_replay(self):
        with tempfile.TemporaryDirectory(prefix="x4-assessment-partial-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")

            def interrupted(_packet):
                raise controller_public_assessment.PublicInterpreterError(
                    "response lost", cost_usd=.03, terminal=False)

            with self.assertRaises(task_executor.ExecutorError):
                executor.assess_public(root, interpreter=interrupted,
                                       **self.inputs(executor, root))
            recorded = executor.status(root)
            self.assertEqual("uncertain", recorded["public_assessment"]["status"])
            self.assertEqual(.03, recorded["budget"]["spent_usd"])
            self.assertEqual([recorded["public_assessment"]["invocation_id"]],
                             recorded["budget"]["unresolved"])
            self.assertEqual([], worker.calls)

    def test_interpreter_terminal_failure_records_final_charge(self):
        with tempfile.TemporaryDirectory(prefix="x4-assessment-terminal-") as raw:
            executor, root, _ = prepare(Path(raw) / "actor", "C03-D1")

            def invalid_json(_packet):
                raise controller_public_assessment.PublicInterpreterError(
                    "terminal output was not structured", cost_usd=.05,
                    terminal=True)

            with self.assertRaises(task_executor.ExecutorError):
                executor.assess_public(root, interpreter=invalid_json,
                                       **self.inputs(executor, root))
            recorded = executor.status(root)
            self.assertEqual("invalid", recorded["public_assessment"]["status"])
            self.assertEqual(.05, recorded["budget"]["spent_usd"])
            self.assertEqual([], recorded["budget"]["unresolved"])

    def test_assessment_over_its_allocation_is_charged_and_blocks_dispatch(self):
        with tempfile.TemporaryDirectory(prefix="x4-assessment-overrun-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")

            def overrun(packet):
                response = interpret_public(packet)
                response["telemetry"] = {"provider_calls": 1,
                                         "model": "claude-sonnet-5", "cost_usd": .75,
                                         "input_tokens": 100, "output_tokens": 20}
                return response

            executor.assess_public(root, interpreter=overrun,
                                   **self.inputs(executor, root))
            recorded = executor.status(root)
            self.assertEqual("blocked", recorded["state"])
            self.assertEqual("settled", recorded["public_assessment"]["status"])
            self.assertEqual(.75, recorded["budget"]["spent_usd"])
            self.assertEqual([], recorded["budget"]["unresolved"])
            self.assertEqual([], worker.calls)

    def test_experimental_n3_cell_is_frozen_before_controller_and_worker(self):
        with tempfile.TemporaryDirectory(prefix="x4-selection-") as raw:
            trial = {"schema_version": 3, "arm": "candidate",
                     "manifest_sha256": "a" * 64, "cost_ceiling_usd": 12.0,
                     "repair_cells": ["worker-sonnet-low", "worker-opus-high"]}
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1",
                                             experimental_dispatch=trial)
            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "selection is not frozen"):
                executor.run(root)
            assessment = executor.assess_public(
                root, interpreter=interpret_public, **self.inputs(executor, root))
            expected = worker_selector.select(
                assessment["worker"],
                supported_cells=set(worker.capability(executor.project)["supported_cells"]),
                remaining_usd=executor.status(root)["budget"]["available_usd"],
                budget_enforced=True)
            frozen = executor.freeze_public_selection(root)
            self.assertEqual(expected["selected_cell"], frozen["ladder"][0])
            self.assertEqual("X4-experimental-n3-v1", frozen["admission"]["policy"])
            self.assertEqual(frozen, executor.freeze_public_selection(root))
            control = controller_control.ControlDecision(
                "auto", "shipped-default", 0,
                assessment["rigour"]["task_revision"], "offline-pair")
            decision = controller_policy.decide(
                assessment["rigour"], control, selected_cell=frozen["ladder"][0])
            self.assertEqual("controller", decision["effective_action"])
            definition = frozen["definition"]
            dispatch = controller_dispatch.TaskDispatcher(
                executor.project, FakeController(), root_task_id=root).dispatch(
                    decision, problem_text=definition["goal"],
                    acceptance_state={"contract_digest": definition[
                        "acceptance_definition"]["contract_digest"]},
                    input_revision=definition["input_revision"])
            self.assertEqual("worker-ready", dispatch["stage"])
            executor.accept_controller_handoff(root, decision["decision_id"])
            result = executor.run(root)
            self.assertEqual("accepted", result["state"])
            self.assertEqual(frozen["ladder"][0], worker.calls[0].requested_cell)

    def test_frozen_controller_decision_survives_later_operator_mode_change(self):
        with tempfile.TemporaryDirectory(prefix="x4-control-freeze-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")
            assessment = executor.assess_public(
                root, interpreter=interpret_public, **self.inputs(executor, root))
            controller_control.set_mode(executor.project, "project", "on")
            control = controller_control.resolve(
                executor.project,
                task_revision=assessment["rigour"]["task_revision"])
            decision = controller_policy.decide(
                assessment["rigour"], control,
                selected_cell=executor.status(root)["ladder"][0])
            frozen = executor.freeze_routing_decision(root, decision)
            self.assertEqual(decision, frozen["routing_decision"]["decision"])
            controller_control.set_mode(executor.project, "project", "off")
            self.assertEqual(frozen["routing_decision"],
                             executor.freeze_routing_decision(
                                 root, decision)["routing_decision"])
            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "Controller decision requires"):
                executor.run(root)
            changed = controller_policy.decide(
                assessment["rigour"], controller_control.resolve(
                    executor.project,
                    task_revision=assessment["rigour"]["task_revision"]),
                selected_cell=frozen["ladder"][0])
            with self.assertRaises(task_executor.ExecutorError):
                executor.freeze_routing_decision(root, changed)
            definition = frozen["definition"]
            forged = controller_policy.decide(
                assessment["rigour"], controller_control.ControlDecision(
                    "on", "explicit", 42, assessment["rigour"]["task_revision"], None),
                selected_cell=frozen["ladder"][0])
            rejected = controller_dispatch.TaskDispatcher(
                executor.project, FakeController(), root_task_id=root).dispatch(
                    forged, problem_text=definition["goal"],
                    acceptance_state={"contract_digest": definition[
                        "acceptance_definition"]["contract_digest"]},
                    input_revision=definition["input_revision"])
            self.assertEqual("blocked", rejected["stage"])
            self.assertIn("frozen N1 routing choice", rejected["error"])
            dispatch = controller_dispatch.TaskDispatcher(
                executor.project, FakeController(), root_task_id=root).dispatch(
                    decision, problem_text=definition["goal"],
                    acceptance_state={"contract_digest": definition[
                        "acceptance_definition"]["contract_digest"]},
                    input_revision=definition["input_revision"])
            self.assertEqual("worker-ready", dispatch["stage"])
            executor.accept_controller_handoff(root, decision["decision_id"])
            self.assertEqual("accepted", executor.run(root)["state"])
            self.assertEqual(1, len(worker.calls))

    def test_cancelled_trial_continuation_requires_fresh_assessment_and_cell(self):
        with tempfile.TemporaryDirectory(prefix="x4-continuation-") as raw:
            trial = {"schema_version": 3, "arm": "candidate",
                     "manifest_sha256": "b" * 64, "cost_ceiling_usd": 12.0,
                     "repair_cells": ["worker-sonnet-low", "worker-opus-high"]}
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1",
                                             experimental_dispatch=trial)
            assessment = executor.assess_public(
                root, interpreter=interpret_public, **self.inputs(executor, root))
            executor.freeze_public_selection(root)
            control = controller_control.resolve(
                executor.project,
                task_revision=assessment["rigour"]["task_revision"])
            decision = controller_policy.decide(
                assessment["rigour"], control,
                selected_cell=executor.status(root)["ladder"][0])
            executor.freeze_routing_decision(root, decision)
            executor.cancel(root, actor="operator", reason="new task revision")
            continued = executor.continue_task(
                root, actor="operator", authority_id="continuation-grant",
                reason="new public evidence")
            self.assertEqual("ready", continued["state"])
            self.assertNotIn("public_assessment", continued)
            self.assertNotIn("routing_decision", continued)
            self.assertEqual("X4-pending-n3-v1", continued["admission"]["policy"])
            self.assertEqual(decision, continued["revision_history"][-1]
                             ["routing_decision"]["decision"])
            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "selection is not frozen"):
                executor.run(root)
            self.assertEqual([], worker.calls)


if __name__ == "__main__":
    unittest.main()
