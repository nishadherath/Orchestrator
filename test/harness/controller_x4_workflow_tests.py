#!/usr/bin/env python3
"""Provider-free X4 interactive-control and one-root workflow checks."""
from __future__ import annotations

import tempfile
import unittest
import contextlib
import io
import json
import sys
from unittest import mock
from pathlib import Path

from test.harness.controller_routing_r4_tests import FakeAdapter as FakeController
from test.harness.controller_x3_pair_tests import interpret_public, prepare
from test.harness.controller_x4_assessment_tests import AssessmentTests

import controller_control
import controller_dispatch
import controller_integrity
import controller_profile_policy
import controller_workflow
import claudep
import dispatch_budget
import system_controller
import task_executor
import worker_adapter


class WorkflowTests(unittest.TestCase):
    def execute(self, executor, root, controller, **overrides):
        options = AssessmentTests().inputs(executor, root)
        options["assessment_allowance_usd"] = options.pop("maximum_usd")
        return controller_workflow.execute(
            executor, root, interpreter=interpret_public,
            controller_adapter=controller, **options, **overrides)

    def test_ordinary_auto_uses_worker_and_resume_never_replays(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-ordinary-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "N04-D1")
            controller = FakeController()
            first = self.execute(executor, root, controller,
                                 worker_attempt_limit=1)
            self.assertEqual("worker", first["decision"]["effective_action"])
            self.assertEqual("accepted", first["task"]["state"])
            self.assertEqual(0, controller.calls)
            self.assertEqual(1, len(worker.calls))
            second = self.execute(executor, root, controller)
            self.assertEqual(first["decision"], second["decision"])
            self.assertEqual(1, len(worker.calls))

    def test_operator_on_forces_controller_for_ordinary_task(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-on-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "N04-D1")
            controller = FakeController()
            result = self.execute(executor, root, controller,
                                  explicit_mode="on", worker_attempt_limit=1)
            self.assertEqual("controller", result["decision"]["effective_action"])
            self.assertEqual("explicit", result["decision"]["override_scope"])
            self.assertEqual("accepted", result["task"]["state"])
            self.assertEqual(1, controller.calls)
            self.assertEqual(1, len(worker.calls))

    def test_controller_worker_can_start_after_investigation_context_exits(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-deferred-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "N04-D1")
            controller = FakeController()
            result = self.execute(executor, root, controller,
                                  explicit_mode="on", worker_attempt_limit=1,
                                  defer_worker=True)
            self.assertEqual("controller", result["decision"]["effective_action"])
            self.assertEqual("worker-ready", result["dispatch"]["stage"])
            self.assertEqual("ready", result["task"]["state"])
            self.assertEqual(1, controller.calls)
            self.assertEqual([], worker.calls)
            resumed = self.execute(executor, root, None,
                                   worker_attempt_limit=1)
            self.assertIsNone(resumed["dispatch"])
            self.assertEqual("accepted", resumed["task"]["state"])
            self.assertEqual(1, controller.calls)
            self.assertEqual(1, len(worker.calls))

    def test_controller_handoff_obeys_one_worker_call_limit_on_failure(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-one-call-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "N04-D1")
            editable = next(path for path in executor.status(root)["definition"]["scope"]
                            if path != "report.json")
            original_run = worker.run

            def fail_run(request):
                receipt = original_run(request)
                (request.actor_root / editable).write_text(
                    "raise AssertionError('fake first failure')\n", encoding="utf-8")
                return receipt

            worker.run = fail_run
            controller = FakeController()
            result = self.execute(executor, root, controller,
                                  explicit_mode="on", worker_attempt_limit=1)
            self.assertEqual("controller", result["decision"]["effective_action"])
            self.assertEqual("ready", result["task"]["state"])
            self.assertEqual(1, controller.calls)
            self.assertEqual(1, len(worker.calls))
            self.assertEqual("worker-sonnet-low", worker.calls[0].requested_cell)
            self.assertEqual("fail", result["task"]["attempts"][0]["verification"]["status"])
            self.assertEqual([], result["task"]["budget"]["unresolved"])

    def test_missing_graft_blocks_before_controller_admission(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-no-graft-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "N04-D1")
            with self.assertRaisesRegex(controller_workflow.WorkflowError,
                                        "Controller host preflight failed"):
                self.execute(executor, root,
                             controller_dispatch.ControllerRuntimeAdapter(),
                             explicit_mode="on")
            state = executor.status(root)
            self.assertEqual("ready", state["state"])
            self.assertIsNone(state.get("controller_admission"))
            self.assertEqual("controller", state["routing_decision"]["decision"]["effective_action"])
            self.assertEqual(0, state["budget"]["reserved_usd"])
            self.assertEqual([], worker.calls)

    def test_live_runner_seals_only_graft_from_project_mcp_config(self):
        with tempfile.TemporaryDirectory(prefix="x4-controller-graft-") as raw:
            project = Path(raw)
            graft_cli = project / "graft-cli.js"
            graft_cli.write_text("// test launcher path\n", encoding="utf-8")
            config = {"mcpServers": {
                "graft": {"command": sys.executable,
                          "args": [str(graft_cli), "mcp", "${CLAUDE_PROJECT_DIR:-.}"]},
                "unrelated": {"command": sys.executable, "args": ["--version"]}}}
            (project / ".mcp.json").write_text(json.dumps(config), encoding="utf-8")
            adapter = controller_dispatch.ControllerRuntimeAdapter()
            self.assertTrue(adapter.capability(project)["graft_only"])
            runner = adapter._factory(project, "standard")(lambda: 4.0)
            args = runner.extra_args
            path = Path(next(part.split("=", 1)[1] for part in args
                             if part.startswith("--mcp-config=")))
            self.assertEqual({"graft"}, set(json.loads(path.read_text(
                encoding="utf-8"))["mcpServers"]))
            grant = next(part for part in args if part.startswith("--allowedTools="))
            self.assertEqual(set(controller_dispatch.GRAFT_READ_TOOLS),
                             set(grant.split("=", 1)[1].split(",")))
            self.assertIn("--strict-mcp-config", args)
            self.assertNotIn("--safe-mode", args)
            self.assertNotIn("Edit", args)
            self.assertNotIn("Bash", args)

    def test_role_ledger_records_graft_init_and_use_without_tool_input(self):
        events = [
            {"type": "system", "subtype": "init",
             "mcp_servers": [{"name": "graft", "status": "connected"}],
             "tools": ["Read", *controller_dispatch.GRAFT_READ_TOOLS]},
            {"type": "assistant", "parent_tool_use_id": None,
             "message": {"model": "claude-opus-5", "content": [
                 {"type": "tool_use", "name": "mcp__graft__graft_check_freshness",
                  "input": {"secret": "must-not-persist"}}]}},
            {"type": "result", "subtype": "success", "result": "done",
             "total_cost_usd": 0.1},
        ]
        _, evidence = claudep._stream_envelope("\n".join(
            json.dumps(row) for row in events))
        self.assertNotIn("must-not-persist", json.dumps(evidence))
        with tempfile.TemporaryDirectory(prefix="x4-role-tool-ledger-") as raw:
            project = Path(raw)
            budget = dispatch_budget.DispatchBudget(project / "budget.json", 1.0)
            budget.reserve("role-probe", 1.0, 0.0, {"role": "framer"})
            budget.start("role-probe")
            role = system_controller.LiveRoleRunner(
                project, budget.remaining, budget=budget)
            result = claudep.ClaudeCallResult(
                "done", 0.1, 1.0, evidence, events[-1], "probe")
            role._account("role-probe", result, final=True,
                          status="completed", identity={})
            telemetry = budget.snapshot()["invocations"]["role-probe"]["telemetry"]
            self.assertEqual([{"name": "graft", "status": "connected"}],
                             telemetry["mcp_servers"])
            self.assertEqual(["mcp__graft__graft_check_freshness"],
                             telemetry["tool_use_names"])
            self.assertNotIn("must-not-persist", json.dumps(telemetry))
            self.assertTrue(controller_dispatch._graft_role_host(budget.snapshot()))
            missing_use = json.loads(json.dumps(budget.snapshot()))
            missing_use["invocations"]["role-probe"]["telemetry"]["tool_use_names"] = []
            self.assertFalse(controller_dispatch._graft_role_host(missing_use))
            disconnected = json.loads(json.dumps(budget.snapshot()))
            disconnected["invocations"]["role-probe"]["telemetry"]["mcp_servers"] = []
            self.assertFalse(controller_dispatch._graft_role_host(disconnected))

    def test_controller_receives_the_complete_frozen_acceptance_contract(self):
        """The live adapter's preflight must pass before a role call exists."""
        class CheckingController(FakeController):
            def run(self, request):
                frozen = controller_integrity.freeze_acceptance(
                    request.acceptance_state)
                if frozen is None:
                    raise AssertionError("Controller acceptance was absent")
                return super().run(request)

        with tempfile.TemporaryDirectory(prefix="x4-workflow-acceptance-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "N04-D1")
            controller = CheckingController()
            result = self.execute(executor, root, controller,
                                  explicit_mode="on")
            self.assertEqual("accepted", result["task"]["state"])
            self.assertEqual("worker-ready", result["dispatch"]["stage"])
            self.assertEqual(1, controller.calls)
            self.assertEqual(1, len(worker.calls))

    def test_session_off_overrides_project_on_for_consequential_task(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-off-") as raw:
            executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")
            controller_control.set_mode(executor.project, "project", "on")
            controller_control.set_mode(executor.project, "session", "off",
                                        session_id="session-1")
            controller = FakeController()
            result = self.execute(executor, root, controller,
                                  session_id="session-1")
            self.assertEqual("worker", result["decision"]["effective_action"])
            self.assertEqual("session", result["decision"]["override_scope"])
            self.assertEqual("accepted", result["task"]["state"])
            self.assertEqual(0, controller.calls)
            self.assertEqual(1, len(worker.calls))

    def test_auto_gap_guides_worker_but_empty_gap_stops(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-gap-") as raw:
            executor, root, worker = prepare(Path(raw) / "good", "C03-D1")
            useful = self.execute(executor, root, FakeController("gap"))
            self.assertEqual("controller", useful["decision"]["effective_action"])
            self.assertEqual("accepted", useful["task"]["state"])
            self.assertIn("Controller evidence", worker.calls[0].issue)

            stopped, stop_root, stop_worker = prepare(Path(raw) / "empty", "C03-D1")
            empty = FakeController("gap-empty")
            blocked = self.execute(stopped, stop_root, empty)
            self.assertEqual("blocked", blocked["task"]["state"])
            self.assertEqual("blocked", blocked["dispatch"]["stage"])
            self.assertEqual([], stop_worker.calls)
            self.assertEqual(.2, blocked["task"]["budget"]["spent_usd"])
            self.assertEqual(1, empty.calls)

    def test_status_distinguishes_current_intent_from_frozen_dispatch(self):
        with tempfile.TemporaryDirectory(prefix="x4-workflow-status-") as raw:
            executor, root, _ = prepare(Path(raw) / "actor", "N04-D1")
            pending = controller_control.status_view(executor.project, root_id=root)
            self.assertEqual("assessment_pending", pending["applicability"])
            self.assertIsNone(pending["effective_action"])

            result = self.execute(executor, root, FakeController(), explicit_mode="on")
            controller_control.set_mode(executor.project, "project", "off")
            view = controller_control.status_view(executor.project, root_id=root)
            self.assertEqual("off", view["current_intent"]["mode"])
            self.assertEqual("project", view["current_intent"]["source"])
            self.assertEqual("decision_frozen", view["applicability"])
            self.assertEqual("controller", view["effective_action"])
            self.assertEqual(result["decision"], view["frozen_decision"])
            self.assertEqual("worker-ready", view["controller_admission_status"])
            self.assertTrue(view["controller_invocation_admitted"])
            self.assertIsNone(view["provider_call_confirmed"])
            self.assertEqual(1, view["worker_attempt_count"])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(0, controller_control.main([
                    "--project", str(executor.project), "status", "--root-id", root]))
            cli = json.loads(output.getvalue())
            self.assertFalse(cli["paid_work_started"])
            self.assertEqual(view, cli["view"])

    def test_profile_policy_retains_standard_and_labels_frontier_trial(self):
        with tempfile.TemporaryDirectory(prefix="x4-profile-") as raw:
            ordinary, ordinary_root, _ = prepare(Path(raw) / "ordinary", "C03-D1")
            standard = self.execute(ordinary, ordinary_root, FakeController())
            selected = standard["task"]["routing_decision"]["profile_selection"]
            self.assertEqual(2, standard["task"]["routing_decision"]["version"])
            self.assertEqual("standard", selected["profile"])
            self.assertEqual("automatic-retained", selected["source"])
            self.assertEqual("retained-prior-only", selected["qualification_claim"])
            with mock.patch.object(controller_profile_policy.model_registry,
                                   "resolve_role_profile",
                                   side_effect=RuntimeError("registry changed")):
                self.assertEqual("accepted", ordinary.status(ordinary_root)["state"])

            rejected, rejected_root, _ = prepare(Path(raw) / "rejected", "C03-D1")
            with self.assertRaisesRegex(controller_profile_policy.ProfilePolicyError,
                                        "experimental admission"):
                self.execute(rejected, rejected_root, FakeController(),
                             controller_profile="frontier-candidate",
                             explicit_experimental_profile=True)
            self.assertIsNone(rejected.status(rejected_root).get("routing_decision"))

            trial = {"schema_version": 3, "arm": "candidate",
                     "manifest_sha256": "a" * 64, "cost_ceiling_usd": 12.0,
                     "repair_cells": ["worker-sonnet-low", "worker-opus-high"]}
            experimental, experimental_root, _ = prepare(
                Path(raw) / "experimental", "C03-D1",
                experimental_dispatch=trial)
            run = self.execute(experimental, experimental_root, FakeController(),
                               controller_profile="frontier-candidate",
                               explicit_experimental_profile=True)
            self.assertEqual("accepted", run["task"]["state"])
            selected = run["task"]["routing_decision"]["profile_selection"]
            self.assertEqual("frontier-candidate", selected["profile"])
            self.assertEqual("explicit-experimental", selected["source"])
            self.assertEqual("none", selected["qualification_claim"])
            self.assertEqual("frontier-candidate",
                             run["decision"]["controller_profile"])

            with self.assertRaisesRegex(controller_profile_policy.ProfilePolicyError,
                                        "cannot reserve"):
                controller_profile_policy.choose(
                    remaining_usd=7.49, experimental_admission=True,
                    requested_profile="frontier-candidate",
                    explicit_experimental=True, follow_on_floor_usd=3.5)

            root_path = ordinary._path(ordinary_root)
            altered = json.loads(root_path.read_text(encoding="utf-8"))
            altered["routing_decision"]["profile_selection"]["source"] = "explicit-retained"
            altered["record_digest"] = task_executor.digest({
                key: value for key, value in altered.items()
                if key != "record_digest"})
            root_path.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "routing decision differs"):
                ordinary.status(ordinary_root)


if __name__ == "__main__":
    unittest.main()
