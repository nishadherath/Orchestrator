#!/usr/bin/env python3
"""Provider-free X4 Controller-to-root worker handoff checks."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test.harness.controller_routing_r4_tests import FakeAdapter as FakeController
from test.harness.controller_x3_pair_tests import assess_and_decide, prepare

import controller_dispatch
import task_executor


class HandoffTests(unittest.TestCase):
    def dispatch(self, project: Path, controller_mode: str = "solution"):
        executor, root, worker = prepare(project, "C03-D1")
        assessment, _, decision = assess_and_decide(executor, root, worker, "auto")
        self.assertEqual("controller", decision["effective_action"])
        record = executor.status(root)
        frozen = record["definition"]
        state = controller_dispatch.TaskDispatcher(
            project, FakeController(controller_mode), root_task_id=root).dispatch(
                decision, problem_text=frozen["goal"],
                acceptance_state={"contract_digest": frozen["acceptance_definition"]
                                  ["contract_digest"]},
                input_revision=frozen["input_revision"])
        return executor, root, worker, decision, state

    def test_validated_handoff_releases_worker_and_preserves_independent_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="controller-x4-handoff-") as raw:
            executor, root, worker, decision, state = self.dispatch(Path(raw) / "actor")
            self.assertEqual("worker-ready", state["stage"])
            accepted = executor.accept_controller_handoff(root, decision["decision_id"])
            self.assertEqual("worker-ready", accepted["controller_admission"]["status"])
            self.assertEqual(.2, accepted["budget"]["spent_usd"])
            self.assertEqual([], accepted["budget"]["unresolved"])
            self.assertEqual(accepted, executor.accept_controller_handoff(
                root, decision["decision_id"]))
            result = executor.run(root)
            self.assertEqual("accepted", result["state"])
            self.assertEqual(.3, result["budget"]["spent_usd"])
            self.assertEqual(1, len(worker.calls))
            self.assertIn("Controller evidence", worker.calls[0].issue)
            self.assertEqual(1, sum(event["kind"] == "controller_handoff_validated"
                                    for event in result["journal"]))

    def test_tampered_packet_keeps_worker_hold_and_blocks_launch(self):
        with tempfile.TemporaryDirectory(prefix="controller-x4-tamper-") as raw:
            project = Path(raw) / "actor"
            executor, root, worker, decision, state = self.dispatch(project)
            packet = project / state["worker_handoff"]["controller_packet"]
            value = json.loads(packet.read_text(encoding="utf-8"))
            value["safe_next_action"] = "skip acceptance"
            packet.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(task_executor.ExecutorError):
                executor.accept_controller_handoff(root, decision["decision_id"])
            with self.assertRaises(task_executor.ExecutorError):
                executor.run(root)
            self.assertEqual([], worker.calls)
            self.assertIn(executor.status(root)["controller_admission"]
                          ["follow_on_invocation_id"],
                          executor.status(root)["budget"]["unresolved"])

    def test_cancelled_root_cannot_accept_late_controller_handoff(self):
        with tempfile.TemporaryDirectory(prefix="controller-x4-cancel-") as raw:
            executor, root, worker, decision, _ = self.dispatch(Path(raw) / "actor")
            executor.cancel(root, actor="operator", reason="stop")
            with self.assertRaises(task_executor.ExecutorError):
                executor.accept_controller_handoff(root, decision["decision_id"])
            self.assertEqual([], worker.calls)


if __name__ == "__main__":
    unittest.main()
