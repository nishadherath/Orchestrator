#!/usr/bin/env python3
"""Exercise the operator CLI against real task records and injected workers."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from task_executor import TaskExecutor  # noqa: E402
from worker_tasks import main, run_observed  # noqa: E402
from worker_executor_n1_tests import FakeAdapter  # noqa: E402


class WorkerTasksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="worker-tasks-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.adapter = FakeAdapter()
        self.contract = {"version": 1, "kind": "command", "criteria": ["accepted output"],
                         "required_outputs": ["output.txt"], "protected_paths": [],
                         "command": [sys.executable, "-c",
                                     "from pathlib import Path; assert Path('output.txt').read_text() == 'accepted'"]}
        self.write("acceptance.json", self.contract)
        self.spec = {"goal": "Create accepted output", "scope": ["output.txt"],
                     "acceptance_path": "acceptance.json", "budget_usd": 1.0,
                     "authority_id": "operator_grant", "actor": "operator", "root_id": "root_a"}

    def write(self, name, value):
        path = self.project / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def call(self, action, request=None, root=None, adapter=None):
        args = [action, "--project", str(self.project), "--json"]
        if request is not None:
            args.extend(["--request", str(self.write("operation.json", request))])
        if root is not None:
            args.extend(["--root", root])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args, adapter=self.adapter if adapter is None else adapter)
        return code, json.loads(out.getvalue() or err.getvalue())

    def test_admit_status_run_and_audit_are_separate(self):
        self.assertEqual((0, "ready"), (lambda x: (x[0], x[1]["state"]))(self.call("admit", self.spec)))
        self.assertEqual([], self.adapter.calls)
        self.assertEqual(2, self.call("audit")[0])
        self.assertEqual("ready", self.call("status", root="root_a")[1]["state"])
        self.assertEqual("accepted", self.call("run", root="root_a")[1]["state"])
        self.assertEqual(1, len(self.adapter.calls))
        self.assertEqual(0, self.call("audit")[0])
        # An accepted root is idempotent and never starts a new paid attempt.
        self.assertEqual(0, self.call("run", root="root_a")[0])
        self.assertEqual(1, len(self.adapter.calls))

    def test_invalid_admission_has_no_side_effect(self):
        for extra in ({"experimental_dispatch": {}}, {"budget_usd": True},
                      {"scope": "output.txt"}, {"acceptance_path": "../outside.json"}):
            self.assertEqual(2, self.call("admit", {**self.spec, **extra})[0])
            self.assertFalse((self.project / ".claude/task-executor-v2").exists())

    def test_b0_failure_sequence_and_cost_are_preserved(self):
        self.adapter.fail_count = 2
        self.call("admit", self.spec)
        code, result = self.call("run", root="root_a")
        self.assertEqual(0, code)
        self.assertEqual(["worker-sonnet-low", "worker-sonnet-low", "worker-opus-high"],
                         [r.requested_cell for r in self.adapter.calls])
        self.assertAlmostEqual(0.3, result["budget"]["spent_usd"])

    def test_cancel_and_linked_continuation_do_not_replenish_budget(self):
        self.call("admit", self.spec)
        authority = {"actor": "operator", "reason": "stop this revision"}
        self.assertEqual("cancelled", self.call("cancel", authority, "root_a")[1]["state"])
        self.assertEqual(2, self.call("resume", authority, "root_a")[0])
        code, continued = self.call("continue", {**authority, "authority_id": "new_revision"}, "root_a")
        self.assertEqual(0, code)
        self.assertEqual(2, continued["revision"]["revision_number"])
        self.assertEqual("accepted", self.call("run", root="root_a")[1]["state"])
        self.assertEqual(1, len(self.adapter.calls))

    def test_durable_cancel_reaches_adapter_owned_by_run(self):
        class WaitingAdapter(FakeAdapter):
            def __init__(self):
                super().__init__()
                self.started, self.stopped = threading.Event(), threading.Event()
            def run(self, request):
                self.started.set()
                if not self.stopped.wait(5):
                    raise AssertionError("cancel was not relayed")
                return super().run(request)
            def cancel(self, invocation):
                self.stopped.set()
                return True
        adapter = WaitingAdapter()
        self.call("admit", self.spec, adapter=adapter)
        executor = TaskExecutor(self.project, adapter)
        results = []
        thread = threading.Thread(target=lambda: results.append(run_observed(executor, "root_a")))
        thread.start()
        self.assertTrue(adapter.started.wait(5))
        # A second CLI driver must not classify an active invocation as a crash.
        self.assertEqual(2, self.call("run", root="root_a", adapter=adapter)[0])
        self.assertEqual("running", self.call("status", root="root_a")[1]["state"])
        # This independent adapter cannot signal the active worker directly.
        TaskExecutor(self.project, FakeAdapter()).cancel("root_a", actor="operator", reason="stop")
        thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertTrue(adapter.stopped.is_set())
        self.assertEqual("cancelled", results[0]["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_missing_mcp_configuration_blocks_admission(self):
        from worker_adapter import WorkerAdapter
        self.assertEqual(2, self.call("admit", self.spec, adapter=WorkerAdapter())[0])
        self.assertEqual([], self.adapter.calls)

    def test_malformed_control_is_rejected_without_changing_task(self):
        self.call("admit", self.spec)
        self.call("cancel", {"actor": "operator", "reason": "stop"}, "root_a")
        before = self.call("status", root="root_a")[1]
        code, error = self.call("continue", {"actor": 42, "reason": "continue",
                                            "authority_id": "bad_actor"}, "root_a")
        self.assertEqual(2, code)
        self.assertIn("actor must be", error["error"])
        self.assertEqual(before, self.call("status", root="root_a")[1])


if __name__ == "__main__":
    unittest.main()
