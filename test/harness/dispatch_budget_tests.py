"""Deterministic Controller admission, failure and recovery regressions.

Only local subprocesses and mocked provider replies run. No model calls.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import claudep
import system_controller as controller
from dispatch_budget import BudgetError, BudgetExhausted, DispatchBudget, InvocationAlreadyStarted


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dispatch-budget-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "dispatch-budget.json"

    def budget(self, limit=0.6):
        return DispatchBudget(self.path, limit)

    def test_race_across_processes_cannot_oversubscribe(self):
        budget = self.budget(1.0)
        child = (
            "import sys; from pathlib import Path; "
            "sys.path.insert(0, sys.argv[1]); "
            "from dispatch_budget import DispatchBudget, BudgetExhausted; "
            "b=DispatchBudget(Path(sys.argv[2]));\n"
            "try: b.reserve(sys.argv[3], .6, .5, {})\n"
            "except BudgetExhausted: pass\n"
        )
        children = [subprocess.Popen([sys.executable, "-c", child, str(ROOT / "tools"),
                                      str(self.path), str(i)], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True) for i in range(6)]
        try:
            outcomes = [(process, process.communicate(timeout=20)) for process in children]
        finally:
            for process in children:
                if process.poll() is None:
                    process.kill()
                process.communicate()
        for process, (out, err) in outcomes:
            self.assertEqual(process.returncode, 0, out + err)
        snap = budget.snapshot()
        self.assertEqual(len(snap["invocations"]), 1)
        self.assertEqual(snap["reserved_usd"], .6)
        self.assertFalse(snap["breached"])

    def test_threads_share_balance(self):
        budget = self.budget(1.2)
        def reserve(i):
            try:
                return DispatchBudget(self.path).reserve(str(i), .6, .5, {})
            except BudgetExhausted:
                return 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertAlmostEqual(sum(pool.map(reserve, range(8))), 1.2)
        self.assertEqual(budget.remaining(), 0)

    def test_reopen_duplicate_dispatch_and_settlement(self):
        budget = self.budget()
        budget.reserve("call", 2, .5, {})
        budget.start("call")
        resumed = DispatchBudget(self.path)
        self.assertEqual(resumed.remaining(), 0)
        with self.assertRaises(InvocationAlreadyStarted):
            resumed.start("call")
        with self.assertRaises(InvocationAlreadyStarted):
            resumed.reserve("call", 2, .5, {})
        args = dict(final=True, telemetry={}, evidence="provider-final")
        resumed.settle("call", .2, **args)
        resumed.settle("call", .2, **args)
        self.assertEqual(resumed.snapshot()["spent_usd"], .2)
        self.assertEqual(resumed.remaining(), .4)
        with self.assertRaises(BudgetError):
            resumed.settle("call", .1, **args)

    def test_partial_usage_holds_unspent_and_final_reconciles(self):
        budget = self.budget()
        budget.reserve("lost", 2, .5, {})
        budget.start("lost")
        budget.settle("lost", .2, final=False, telemetry={}, evidence="timeout")
        snap = DispatchBudget(self.path).snapshot()
        self.assertEqual((snap["spent_usd"], snap["reserved_usd"], snap["available_usd"]), (.2, .4, 0))
        budget.settle("lost", .3, final=True, telemetry={}, evidence="invoice-final")
        self.assertEqual(budget.remaining(), .3)

    def test_overrun_records_truth_and_blocks(self):
        budget = self.budget()
        budget.reserve("over", 2, .5, {})
        budget.start("over")
        budget.settle("over", .8, final=True, telemetry={}, evidence="provider-final")
        self.assertTrue(budget.snapshot()["breached"])
        with self.assertRaises(BudgetExhausted):
            budget.reserve("next", 2, .5, {})

    def test_invalid_limits_and_corruption_fail_closed(self):
        for value in (-1, float("nan"), float("inf"), True, "0.2"):
            with self.assertRaises(BudgetError):
                self.budget(value)
        budget = self.budget(0)
        with self.assertRaises(BudgetExhausted):
            budget.reserve("no", 2, 0, {})
        self.path.write_text('{"version":', encoding="utf-8")
        with self.assertRaises(BudgetError):
            DispatchBudget(self.path)

    def test_cancel_retains_holds_and_blocks_start(self):
        budget = self.budget()
        budget.reserve("queued", 2, .5, {})
        budget.cancel()
        with self.assertRaises(BudgetExhausted):
            budget.start("queued")
        self.assertEqual(budget.snapshot()["reserved_usd"], .6)

    def test_failed_atomic_replace_preserves_balance(self):
        budget = self.budget()
        original = self.path.read_bytes()
        with mock.patch.object(Path, "replace", side_effect=OSError("injected")):
            with self.assertRaises(OSError):
                budget.reserve("no-launch", 2, .5, {})
        self.assertEqual(self.path.read_bytes(), original)

    def runner(self, budget):
        return controller.LiveRoleRunner(self.root, budget.remaining, budget=budget)

    def test_role_cap_is_reservation_not_constant(self):
        budget = self.budget()
        reply = claudep.ClaudeCallResult("", .1, 1, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", return_value=reply) as call:
            self.runner(budget)("frame", "framer", "test", timeout=1)
        self.assertEqual(call.call_args.kwargs["max_budget_usd"], .6)
        self.assertEqual(budget.snapshot()["spent_usd"], .1)

    def test_role_failure_keeps_partial_cost(self):
        budget = self.budget()
        partial = claudep.ClaudeCallResult("", .2, 1, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", side_effect=claudep.ClaudeCallError("timeout", partial)):
            with self.assertRaises(controller.RoleCallFailed):
                self.runner(budget)("frame", "framer", "test", timeout=1)
        snap = budget.snapshot()
        self.assertEqual((snap["spent_usd"], snap["reserved_usd"]), (.2, .4))

    def test_classifier_failure_persists_cost_before_fallback(self):
        budget = self.budget()
        partial = claudep.ClaudeCallResult("", .04, 1, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", side_effect=claudep.ClaudeCallError("bad response", partial)):
            result, _ = self.runner(budget).classify("controller-stability", "test", {}, {"stable": False})
        self.assertEqual(result, {"stable": False})
        self.assertEqual(budget.snapshot()["spent_usd"], .04)
        self.assertEqual(budget.snapshot()["reserved_usd"], .06)

    def test_unknown_success_never_becomes_zero(self):
        budget = self.budget()
        reply = claudep.ClaudeCallResult("", None, 1, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", return_value=reply):
            self.runner(budget)("frame", "framer", "test", timeout=1)
        row = next(iter(budget.snapshot()["invocations"].values()))
        self.assertIsNone(row["cost_usd"])
        self.assertEqual(budget.remaining(), 0)

    def test_failed_run_still_writes_report_and_budget_projection(self):
        partial = claudep.ClaudeCallResult("", .2, 1, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", side_effect=claudep.ClaudeCallError("timeout", partial)):
            result = controller.run_quick("test", self.root, .6, 1,
                                         lambda remaining: controller.LiveRoleRunner(self.root, remaining))
        self.assertEqual(result.outcome, "gap")
        self.assertEqual(result.total_cost_usd, .2)
        self.assertTrue((result.run_dir / "REPORT.md").is_file())
        status = json.loads((result.run_dir / "run-status.json").read_text())
        self.assertEqual((status["execution_status"], status["outcome"]), ("blocked", "gap"))
        row = json.loads((result.run_dir / "budget.jsonl").read_text())
        self.assertEqual(row["cost_usd"], .2)
        self.assertEqual(row["accounting_status"], "uncertain")

    def test_recovery_is_idempotent_and_never_calls_provider(self):
        budget = self.budget()
        budget.reserve("lost", .6, .5, {"phase": "frame", "role": "framer", "cell": "worker-opus-high"})
        budget.start("lost")
        budget.settle("lost", .1, final=False, telemetry={"result": "paid output"}, evidence="partial")
        with mock.patch.object(claudep, "call_claude") as provider:
            first = controller.recover_run(self.root)
            second = controller.recover_run(self.root)
            self.assertEqual(first, second)
            self.assertEqual(first["reserved_usd"], .5)
            options = dict(invocation_id="lost", final_cost_usd=.2, evidence="invoice:example")
            final = controller.recover_run(self.root, **options)
            before = self.path.read_bytes()
            self.assertEqual(controller.recover_run(self.root, **options), final)
            self.assertEqual(self.path.read_bytes(), before)
            provider.assert_not_called()
        self.assertEqual(final["spent_usd"], .2)
        self.assertEqual(final["reserved_usd"], 0)
        row = budget.snapshot()["invocations"]["lost"]
        self.assertEqual(row["telemetry"]["result"], "paid output")
        self.assertEqual(len(row["prior_resolutions"]), 1)
        self.assertTrue((self.root / "RECOVERY.md").is_file())
        schemas = controller.validate_records.load_schemas()
        projected = json.loads((self.root / "budget.jsonl").read_text())
        self.assertEqual(controller.validate_records.validate_record(projected, schemas), [])

    def test_active_run_cannot_be_reconciled(self):
        self.budget()
        with controller.ledger_lock(self.root / "controller-owner", timeout_s=0):
            with self.assertRaises(controller.LedgerLockTimeout):
                controller.recover_run(self.root)

    def test_reused_run_id_cannot_silently_reset_budget(self):
        with mock.patch.object(claudep, "call_claude") as provider:
            args = ("test", self.root, 0, 1, lambda remaining: controller.LiveRoleRunner(self.root, remaining))
            controller.run_quick(*args, run_id="same")
            with self.assertRaises(BudgetError):
                controller.run_quick(*args, run_id="same")
            provider.assert_not_called()

    def test_parallel_live_roles_cannot_share_an_allowance(self):
        budget = self.budget(1.2)
        entered, release = threading.Event(), threading.Event()
        def paid(*args, **kwargs):
            entered.set()
            self.assertTrue(release.wait(5))
            return claudep.ClaudeCallResult("", .1, 1, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", side_effect=paid) as provider:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(self.runner(budget), "generate", "generator", "test", timeout=1)
                try:
                    self.assertTrue(entered.wait(5))
                    second = pool.submit(self.runner(budget), "generate", "generator", "test", timeout=1)
                    with self.assertRaises(BudgetExhausted):
                        second.result(timeout=5)
                    self.assertEqual(budget.snapshot()["reserved_usd"], 1.2)
                finally:
                    release.set()
                first.result(timeout=5)
            self.assertEqual(provider.call_count, 1)

    def test_successful_sibling_survives_parallel_failure(self):
        canned = controller._canned()
        class ScriptedLive(controller.LiveRoleRunner):
            def __init__(self, *args):
                super().__init__(*args)
                self.frames = 0
                self.generators = 0
                self.lock = threading.Lock()
            def __call__(self, phase, role, prompt, *, timeout):
                if phase == "frame":
                    self.frames += 1
                    return controller.RoleReply(canned[f"frame_v{self.frames}"], None)
                if phase == "verify":
                    return controller.RoleReply(canned["measurement"], None)
                if phase == "generate":
                    with self.lock:
                        self.generators += 1
                        number = self.generators
                    if number == 1:
                        raise controller.RoleCallFailed("injected sibling failure")
                    return controller.RoleReply(canned["candidate"] if number == 2 else [], None)
                raise AssertionError(phase)
            def classify(self, phase, prompt, schema, default):
                return default, None
        result = controller.run_quick("test", self.root, 4, 1, lambda remaining: ScriptedLive(self.root, remaining))
        records = [json.loads(line) for line in (result.run_dir / "ledger.jsonl").read_text().splitlines()]
        self.assertEqual(result.outcome, "gap")
        self.assertTrue(any(row["type"] == "CandidateRecord" and row["technique"] == "subtract" for row in records))

    def test_output_ceiling_is_child_local(self):
        original = os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS")
        completed = subprocess.CompletedProcess([], 0, '{"type":"result","total_cost_usd":0}', '')
        with mock.patch.object(claudep.subprocess, "run", return_value=completed) as process:
            claudep.call_claude("test", cwd=self.root, max_output_tokens=1234)
        self.assertEqual(process.call_args.kwargs["env"]["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "1234")
        self.assertEqual(os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS"), original)

    def test_elapsed_limit_covers_classifiers(self):
        runner = self.runner(self.budget())
        runner.deadline = time.monotonic() + .5
        reply = claudep.ClaudeCallResult("{}", 0, 0, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", return_value=reply) as provider:
            runner.classify("controller-stability", "test", {}, {})
            self.assertLessEqual(provider.call_args.kwargs["timeout"], .5)
            runner.deadline = time.monotonic() - 1
            runner.classify("controller-stability", "test", {}, {})
            with self.assertRaises(BudgetExhausted):
                runner("frame", "framer", "test", timeout=1)
            self.assertEqual(provider.call_count, 1)

    def test_interrupt_retains_unknown_charge_and_writes_report(self):
        with mock.patch.object(claudep, "call_claude", side_effect=KeyboardInterrupt):
            result = controller.run_quick("test", self.root, .6, 1,
                                         lambda remaining: controller.LiveRoleRunner(self.root, remaining))
        snap = DispatchBudget(result.run_dir / "dispatch-budget.json").snapshot()
        self.assertTrue(snap["cancelled"])
        self.assertEqual(snap["reserved_usd"], .6)
        self.assertFalse(result.accounting_complete)
        self.assertTrue((result.run_dir / "REPORT.md").is_file())

    def test_invalid_telemetry_cannot_erase_known_charge(self):
        budget = self.budget()
        reply = claudep.ClaudeCallResult("", .2, float("nan"), {"usage": {"input_tokens": -3, "output_tokens": "bad"}}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", return_value=reply):
            self.runner(budget)("frame", "framer", "test", timeout=1)
        row = next(iter(budget.snapshot()["invocations"].values()))
        self.assertEqual(row["cost_usd"], .2)
        self.assertIsNone(row["telemetry"]["wall_clock_s"])
        self.assertIsNone(row["telemetry"]["usage"]["input_tokens"])

    def test_terminal_failure_releases_only_proven_unused_allowance(self):
        budget = self.budget()
        partial = claudep.ClaudeCallResult("", .2, 1, {}, {"type": "result"}, "fake")
        with mock.patch.object(claudep, "call_claude", side_effect=claudep.ClaudeCallError("failed", partial)):
            with self.assertRaises(controller.RoleCallFailed):
                self.runner(budget)("frame", "framer", "test", timeout=1)
        self.assertEqual(budget.remaining(), .4)
        self.assertEqual(budget.snapshot()["spent_usd"], .2)

    def test_malformed_reply_keeps_allowance(self):
        completed = subprocess.CompletedProcess([], 0, 'truncated', '')
        budget = self.budget()
        with mock.patch.object(claudep.subprocess, "run", return_value=completed):
            with self.assertRaises(controller.RoleCallFailed):
                self.runner(budget)("frame", "framer", "test", timeout=1)
        self.assertEqual(budget.snapshot()["reserved_usd"], .6)

    def test_process_death_does_not_refund_or_allow_duplicate_start(self):
        self.budget()
        child = (
            "import os,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
            "from dispatch_budget import DispatchBudget; from route import ledger_lock; "
            "b=DispatchBudget(Path(sys.argv[2]));\n"
            "with ledger_lock(Path(sys.argv[2]).parent/'controller-owner'):\n"
            " b.reserve('crashed',.6,.5,{'phase':'frame','role':'framer','cell':'worker-opus-high'}); "
            "b.start('crashed'); os._exit(7)\n"
        )
        process = subprocess.run([sys.executable, "-c", child, str(ROOT / "tools"), str(self.path)],
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 7, process.stderr)
        self.assertEqual(controller.recover_run(self.root)["reserved_usd"], .6)
        with self.assertRaises(InvocationAlreadyStarted):
            DispatchBudget(self.path).start("crashed")

    def test_retry_gets_only_the_remaining_allowance(self):
        budget = self.budget(1)
        reply = claudep.ClaudeCallResult("not a valid record", .4, 1, {}, {}, "fake")
        with mock.patch.object(claudep, "call_claude", return_value=reply) as provider:
            runner = self.runner(budget)
            runner("frame", "framer", "test", timeout=1)
            runner("frame", "framer", "retry", timeout=1)
            with self.assertRaises(BudgetExhausted):
                runner("frame", "framer", "third", timeout=1)
        self.assertEqual([call.kwargs["max_budget_usd"] for call in provider.call_args_list], [1, .6])
        self.assertEqual(budget.snapshot()["spent_usd"], .8)

    def test_timeout_with_partial_terminal_envelope_still_holds(self):
        budget = self.budget()
        expired = subprocess.TimeoutExpired("claude", 1, output=b'{"type":"result","total_cost_usd":0.2}')
        with mock.patch.object(claudep.subprocess, "run", side_effect=expired):
            with self.assertRaises(controller.RoleCallFailed):
                self.runner(budget)("frame", "framer", "test", timeout=1)
        self.assertEqual(budget.snapshot()["spent_usd"], .2)
        self.assertEqual(budget.snapshot()["reserved_usd"], .4)

    def test_deadline_expiring_during_admission_never_launches(self):
        budget = self.budget()
        runner = self.runner(budget)
        runner.deadline = time.monotonic() + 10
        start = budget.start
        def delayed_start(ident):
            start(ident)
            runner.deadline = time.monotonic() - 1
        with mock.patch.object(budget, "start", side_effect=delayed_start):
            with mock.patch.object(claudep, "call_claude") as provider:
                with self.assertRaises(BudgetExhausted):
                    runner("frame", "framer", "test", timeout=1)
                provider.assert_not_called()
        self.assertEqual(budget.remaining(), .6)

    def test_internal_controller_error_leaves_interrupted_status(self):
        class DefectiveRunner:
            def __call__(self, *args, **kwargs):
                raise AssertionError("injected invariant failure")
            def classify(self, phase, prompt, schema, default):
                return default, None
        with self.assertRaisesRegex(AssertionError, "injected invariant"):
            controller.run_quick("test", self.root, 1, 1,
                                 lambda remaining: DefectiveRunner(), run_id="interrupted")
        path = self.root / "runs" / "interrupted" / "run-status.json"
        status = json.loads(path.read_text())
        self.assertEqual(status["execution_status"], "interrupted")
        self.assertIn("AssertionError", status["error"])


if __name__ == "__main__":
    unittest.main()
