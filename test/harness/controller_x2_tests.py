#!/usr/bin/env python3
"""Provider-free X2 checks for named Generator cells and root-owned admission."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_control  # noqa: E402
import controller_dispatch  # noqa: E402
import controller_policy  # noqa: E402
import controller_x0_probe  # noqa: E402
import model_registry  # noqa: E402
import system_controller  # noqa: E402
import task_executor  # noqa: E402
from dispatch_budget import BudgetExhausted, DispatchBudget  # noqa: E402


class OfflineWorker:
    def capability(self, project):
        return {"configured": True, "actor_root": str(project.resolve()),
                "enforcement_proven": False}

    def run(self, request):
        raise AssertionError("N1 worker must wait for Controller handoff integration")


class CountingController:
    def __init__(self, entered=None, release=None, on_call=None):
        self.calls = []
        self.entered, self.release, self.on_call = entered, release, on_call

    def run(self, request):
        self.calls.append(request)
        if self.on_call:
            self.on_call()
        if self.entered:
            self.entered.set()
        if self.release and not self.release.wait(5):
            raise RuntimeError("offline Controller release timed out")
        # A settled gap without a packet is deliberately not worker-ready.
        return {"terminal": True, "accounting_complete": True,
                "cost_usd": .2, "outcome": "gap"}


class X2Tests(unittest.TestCase):
    def test_quick_pipeline_passes_named_techniques_to_live_role_interface(self):
        with tempfile.TemporaryDirectory(prefix="controller-x2-pipeline-") as raw:
            project = Path(raw)
            observed = []
            scripted = system_controller.FakeRoleRunner(
                system_controller._happy_path_script(),
                {"controller-stability": {"stable": True, "reasoning": "verified"},
                 "controller-families": {
                     "families": list(model_registry.GENERATOR_TECHNIQUES),
                     "reasoning": "all three are material"}})
            canned = system_controller._canned()

            class Capture(system_controller.LiveRoleRunner):
                def __call__(self, phase, role, prompt, *, timeout,
                             technique=None, call_cap_usd=None):
                    if phase == "generate":
                        observed.append((technique, call_cap_usd, prompt))
                        records = canned["candidate"] if technique == "subtract" else []
                        return system_controller.RoleReply(records, None)
                    return scripted(phase, role, prompt, timeout=timeout)

                def classify(self, phase, prompt, schema, default):
                    return scripted.classify(phase, prompt, schema, default)

            system_controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                project, 8.0, 1.0,
                lambda remaining: Capture(project, remaining,
                                          role_profile="frontier-candidate"),
                integrity_policy=system_controller.integrity.LEGACY_QUICK_V0)
            self.assertEqual(set(model_registry.GENERATOR_TECHNIQUES),
                             {row[0] for row in observed})
            self.assertEqual(3, len(observed))
            self.assertTrue(all(cap is not None and cap >= .5 and cap <= 2.0
                                for _, cap, _ in observed))
            self.assertEqual(3, len({prompt for _, _, prompt in observed}))

    def test_legacy_decision_ids_cannot_admit_twice_on_one_revision(self):
        with tempfile.TemporaryDirectory(prefix="controller-x2-legacy-race-") as raw:
            project = Path(raw) / "project"
            problem, revision, assessment, acceptance = controller_x0_probe.task_inputs(project)
            decisions = [controller_policy.decide(
                assessment, controller_control.ControlDecision(
                    mode, "explicit", 1, assessment["task_revision"], "offline-test"))
                for mode in ("auto", "on")]
            entered, release = threading.Event(), threading.Event()
            adapter = CountingController(entered, release)

            def dispatch(decision):
                return controller_dispatch.TaskDispatcher(project, adapter).dispatch(
                    decision, problem_text=problem, input_revision=revision,
                    acceptance_state=acceptance)

            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(dispatch, decisions[0])
                self.assertTrue(entered.wait(5))
                second = dispatch(decisions[1])
                release.set()
                first.result(timeout=10)
            self.assertEqual("blocked", second["stage"])
            self.assertEqual(1, len(adapter.calls))

    def test_named_frontier_generator_cells_and_complete_plan(self):
        profile = model_registry.resolve_role_profile("frontier-candidate")
        self.assertEqual(
            {"subtract": "worker-sonnet-high", "re-represent": "worker-opus-xhigh",
             "abduce": "worker-fable-high"},
            {key: value["name"] for key, value in profile["generator_techniques"].items()})
        with tempfile.TemporaryDirectory(prefix="controller-x2-generator-") as raw:
            result = controller_x0_probe.generator_dispatch(Path(raw) / "run")
            self.assertEqual(set(profile["generator_techniques"][family]["name"]
                                 for family in model_registry.GENERATOR_TECHNIQUES),
                             set(result["distinct_dispatched_cells"]))
            self.assertEqual(.03, result["known_spend_usd"])
            budget = DispatchBudget(Path(raw) / "run" / "budget.json")
            techniques = {row["metadata"]["technique"]: row["metadata"]["cell"]
                          for row in budget.snapshot()["invocations"].values()}
            self.assertEqual(
                {family: cell["name"] for family, cell in
                 profile["generator_techniques"].items()}, techniques)
            self.assertTrue(all(row["allowance_units"] <= 1_000_000_000
                                for row in budget.snapshot()["invocations"].values()))
        with tempfile.TemporaryDirectory(prefix="controller-x2-plan-") as raw:
            budget = DispatchBudget(Path(raw) / "budget.json", 2.0)
            runner = system_controller.LiveRoleRunner(
                Path(raw), budget.remaining, budget=budget,
                role_profile="frontier-candidate")
            with self.assertRaises(BudgetExhausted):
                runner.generator_plan(list(model_registry.GENERATOR_TECHNIQUES))
            with self.assertRaisesRegex(ValueError, "named technique"):
                runner("generate", "generator", "independent prompt", timeout=1)
            self.assertEqual({}, budget.snapshot()["invocations"])

    def _root_case(self, project: Path):
        (project / "protected.txt").write_text("fixed", encoding="utf-8")
        contract_path = project / "acceptance.json"
        contract_path.write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["output accepted"],
            "constraints": [], "required_outputs": ["output.txt"],
            "protected_paths": ["protected.txt"],
            "command": [sys.executable, "-c", "raise SystemExit(0)"],
            "timeout_s": 10}), encoding="utf-8")
        problem = "Create accepted output"
        executor = task_executor.TaskExecutor(project, OfflineWorker())
        root_id = executor.admit(
            goal=problem, scope=["output.txt"], permissions=["read", "edit"],
            acceptance_path=contract_path, budget_usd=8.0,
            authority_id="offline-controller-grant", actor="offline-test",
            root_id="controller-root")
        status = executor.status(root_id)
        frozen = status["definition"]["acceptance_definition"]
        acceptance_state = {"contract": frozen["contract"],
                            "contract_digest": frozen["contract_digest"]}
        revision = status["definition"]["input_revision"]
        task_revision = controller_policy.derive_task_revision(problem, project, revision)
        assessment = {
            "assessment_version": 1, "task_revision": task_revision,
            "consequence": "consequential", "premise_uncertainty": "contradictory",
            "alternatives": "several-material", "constraint_coupling": "cross-module",
            "verification_gap": "incomplete-checks", "observed_failure_cause": "none",
            "required_output": "patch", "evidence_availability": "available",
            "deadline": None, "authorised_task_budget_usd": 8.0,
            "evidence": [{"id": "ev-1", "provenance": "repository-artefact",
                          "observed_at": "fixture-clock", "scope": "source and tests",
                          "claim": "two material observations conflict", "material": True}],
        }
        decisions = [controller_policy.decide(
            assessment, controller_control.ControlDecision(
                mode, "explicit", 1, task_revision, "offline-test"))
            for mode in ("auto", "on")]
        self.assertEqual(["controller", "controller"],
                         [item["effective_action"] for item in decisions])
        self.assertNotEqual(decisions[0]["decision_id"], decisions[1]["decision_id"])
        return executor, root_id, problem, revision, acceptance_state, decisions

    def test_two_decisions_share_one_n1_revision_and_root_budget(self):
        with tempfile.TemporaryDirectory(prefix="controller-x2-admission-") as raw:
            project = Path(raw)
            executor, root_id, problem, revision, acceptance, decisions = self._root_case(project)
            entered, release = threading.Event(), threading.Event()
            adapter = CountingController(entered, release)

            def dispatch(decision):
                return controller_dispatch.TaskDispatcher(
                    project, adapter, root_task_id=root_id).dispatch(
                    decision, problem_text=problem, input_revision=revision,
                    acceptance_state=acceptance)

            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(dispatch, decisions[0])
                self.assertTrue(entered.wait(5))
                loser = dispatch(decisions[1])
                release.set()
                winner = first.result(timeout=10)
            self.assertEqual("blocked", loser["stage"])
            self.assertIn("task revision already owns", loser["error"])
            self.assertEqual("blocked", winner["stage"])  # no valid packet
            self.assertEqual(1, len(adapter.calls))
            self.assertEqual("blocked", dispatch(decisions[0])["stage"])
            self.assertEqual(1, len(adapter.calls))
            status = executor.status(root_id)
            self.assertEqual(.2, status["budget"]["spent_usd"])
            self.assertEqual(3.5, status["budget"]["reserved_usd"])
            self.assertEqual([status["controller_admission"]["follow_on_invocation_id"]],
                             status["budget"]["unresolved"])
            self.assertEqual(1, sum(row["kind"] == "controller_admitted"
                                    for row in status["journal"]))
            self.assertEqual(status["revision"]["revision_id"],
                             status["controller_admission"]["revision_id"])
            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "Controller admission is owned"):
                executor.run(root_id)

    def test_cancellation_during_controller_retains_charge_and_blocks_handoff(self):
        with tempfile.TemporaryDirectory(prefix="controller-x2-cancel-") as raw:
            project = Path(raw)
            executor, root_id, problem, revision, acceptance, decisions = self._root_case(project)
            dispatcher = None

            def cancel():
                dispatcher.cancel(decisions[0]["decision_id"])

            adapter = CountingController(on_call=cancel)
            dispatcher = controller_dispatch.TaskDispatcher(
                project, adapter, root_task_id=root_id)
            result = dispatcher.dispatch(
                decisions[0], problem_text=problem,
                input_revision=revision, acceptance_state=acceptance)
            self.assertEqual("blocked", result["stage"])
            self.assertIn("cancellation", result["error"])
            self.assertEqual(1, len(adapter.calls))
            budget = executor.status(root_id)["budget"]
            self.assertEqual(.2, budget["spent_usd"])
            self.assertTrue(budget["cancelled"])
            self.assertEqual([], budget["unresolved"])

    def test_root_cancel_releases_unused_hold_and_links_new_revision(self):
        with tempfile.TemporaryDirectory(prefix="controller-x2-new-revision-") as raw:
            project = Path(raw)
            executor, root_id, problem, revision, acceptance, decisions = self._root_case(project)
            adapter = CountingController()
            dispatcher = controller_dispatch.TaskDispatcher(
                project, adapter, root_task_id=root_id)
            dispatcher.dispatch(decisions[0], problem_text=problem,
                                input_revision=revision, acceptance_state=acceptance)
            prior = executor.status(root_id)
            self.assertEqual(3.5, prior["budget"]["reserved_usd"])
            cancelled = executor.cancel(root_id, actor="operator", reason="change task")
            self.assertEqual("cancelled", cancelled["state"])
            self.assertEqual([], cancelled["budget"]["unresolved"])
            self.assertEqual(.2, cancelled["budget"]["spent_usd"])
            fresh = executor.continue_task(
                root_id, actor="operator", authority_id="new-revision-grant",
                reason="explicitly revised task")
            self.assertEqual("ready", fresh["state"])
            self.assertNotEqual(prior["revision"]["revision_id"],
                                fresh["revision"]["revision_id"])
            self.assertNotIn("controller_admission", fresh)
            self.assertEqual(prior["controller_admission"],
                             fresh["revision_history"][-1]["controller_admission"])

    def test_pre_x2_controller_state_blocks_a_new_claim(self):
        with tempfile.TemporaryDirectory(prefix="controller-x2-legacy-") as raw:
            project = Path(raw)
            executor, root_id, problem, revision, acceptance, decisions = self._root_case(project)
            legacy = project / ".claude" / "controller-dispatch" / "rtd-archived"
            legacy.mkdir(parents=True)
            (legacy / "dispatch-state.json").write_text(json.dumps({
                "decision": {"task_revision": decisions[0]["task_revision"]},
                "controller_invocations": 1, "stage": "blocked"}), encoding="utf-8")
            adapter = CountingController()
            result = controller_dispatch.TaskDispatcher(
                project, adapter, root_task_id=root_id).dispatch(
                    decisions[0], problem_text=problem,
                    input_revision=revision, acceptance_state=acceptance)
            self.assertEqual("blocked", result["stage"])
            self.assertIn("legacy Controller admission", result["error"])
            self.assertEqual([], adapter.calls)
            self.assertNotIn("controller_admission", executor.status(root_id))

    def test_uncertain_controller_charge_keeps_root_closed(self):
        with tempfile.TemporaryDirectory(prefix="controller-x2-uncertain-") as raw:
            project = Path(raw)
            executor, root_id, problem, revision, acceptance, decisions = self._root_case(project)

            class Uncertain(CountingController):
                def run(self, request):
                    self.calls.append(request)
                    return {"terminal": False, "accounting_complete": False,
                            "cost_usd": .2, "outcome": "interrupted"}

            adapter = Uncertain()
            dispatcher = controller_dispatch.TaskDispatcher(
                project, adapter, root_task_id=root_id)
            first = dispatcher.dispatch(decisions[0], problem_text=problem,
                                        input_revision=revision,
                                        acceptance_state=acceptance)
            self.assertEqual("blocked", first["stage"])
            budget = executor.status(root_id)["budget"]
            self.assertEqual(.2, budget["spent_usd"])
            self.assertGreater(budget["reserved_usd"], 3.5)
            self.assertEqual(2, len(budget["unresolved"]))
            second = controller_dispatch.TaskDispatcher(
                project, adapter, root_task_id=root_id).dispatch(
                    decisions[1], problem_text=problem,
                    input_revision=revision, acceptance_state=acceptance)
            self.assertEqual("blocked", second["stage"])
            self.assertEqual(1, len(adapter.calls))


if __name__ == "__main__":
    unittest.main()
