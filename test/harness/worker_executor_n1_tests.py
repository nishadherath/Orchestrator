#!/usr/bin/env python3
"""Offline N1 executor checks with observable fake worker calls."""
from __future__ import annotations

import json
import datetime as dt
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from dispatch_budget import BudgetError, DispatchBudget  # noqa: E402
from task_executor import TaskExecutor, ExecutorError, EDGES, _read, _write, audit, legacy_attempt, transition  # noqa: E402
from worker_adapter import WorkerAdapter, WorkerRequest, CapabilityError, digest  # noqa: E402


class FakeAdapter:
    def __init__(self, fail_count=0):
        self.calls = []
        self.fail_count = fail_count

    def capability(self, root):
        return {"configured": True, "actor_root": str(root.resolve()), "enforcement_proven": False}

    def run(self, request):
        self.calls.append(request)
        if len(self.calls) > self.fail_count:
            (request.actor_root / "output.txt").write_text("accepted", encoding="utf-8")
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": ("claude-opus-5" if request.requested_cell == "worker-opus-high"
                                 else "claude-sonnet-5"),
                "identity_valid": True, "child_models": [], "status": "completed",
                "terminal": True, "writer_stopped": True, "cost_usd": 0.1,
                "usage": {"cost_usd": 0.1, "cost_source": "provider_reported",
                          "currency": "USD", "input_tokens": 10, "output_tokens": 10,
                          "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                "effort_evidence": ("cli-argument:high" if request.requested_cell == "worker-opus-high"
                                    else "cli-argument:low"), "started_at": "2026-09-24T00:00:00Z",
                "finished_at": "2026-09-24T00:00:01Z", "wall_clock_s": 1.0}


class IncompleteAdapter(FakeAdapter):
    def run(self, request):
        result = super().run(request)
        result.update(terminal=False, writer_stopped=False, cost_usd=None,
                      status="interrupted")
        result["usage"].update(cost_usd=None, cost_source="unknown", currency=None)
        return result


class CancellingAdapter(FakeAdapter):
    def __init__(self):
        super().__init__()
        self.executor = None
        self.root = None

    def run(self, request):
        result = super().run(request)
        self.executor.cancel(self.root, actor="operator", reason="deadline")
        return result


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="worker-n1-")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.project.joinpath("protected.txt").write_text("fixed", encoding="utf-8")
        self.contract = self.project / "acceptance.json"
        self.contract.write_text(json.dumps({"version": 1, "kind": "command",
            "criteria": ["output accepted"], "constraints": [],
            "required_outputs": ["output.txt"], "protected_paths": ["protected.txt"],
            "command": [sys.executable, "-c", "from pathlib import Path; import sys; sys.exit(0 if Path('output.txt').read_text() == 'accepted' else 1)"],
            "timeout_s": 10}), encoding="utf-8")

    def make(self, fail_count=0, root="root_a"):
        (self.project / "output.txt").unlink(missing_ok=True)
        adapter = FakeAdapter(fail_count)
        executor = TaskExecutor(self.project, adapter)
        executor.admit(goal="Create accepted output", scope=["output.txt"],
                       permissions=["read", "edit"], acceptance_path=self.contract,
                       budget_usd=1.0, authority_id="grant_" + root,
                       actor="operator", root_id=root)
        return executor, adapter

    def test_exact_b0_success_and_exhaustion(self):
        for failures, expected in ((0, "accepted"), (1, "accepted"), (2, "accepted"), (3, "failed")):
            with self.subTest(failures=failures):
                executor, adapter = self.make(failures, f"root_{failures}")
                result = executor.run(f"root_{failures}")
                self.assertEqual(expected, result["state"])
                self.assertEqual(min(failures + 1, 3), len(adapter.calls))
                self.assertEqual(["worker-sonnet-low", "worker-sonnet-low", "worker-opus-high"][:len(adapter.calls)],
                                 [r.requested_cell for r in adapter.calls])
                self.assertAlmostEqual(len(adapter.calls) * 0.1, result["budget"]["spent_usd"])
                self.assertEqual(1, result["revision"]["revision_number"])
                self.assertEqual("B0", result["admission"]["policy"])
                self.assertTrue(all(legacy_attempt(a, n)["start_kind"] ==
                                    ("direct" if n == 1 else "escalation")
                                    for n, a in enumerate(result["attempts"], 1)))

    def test_authority_and_budget_amendment(self):
        executor, adapter = self.make()
        with self.assertRaises(ExecutorError):
            executor.admit(goal="Other", scope=["output.txt"], permissions=["read", "edit"],
                           acceptance_path=self.contract, budget_usd=1,
                           authority_id="grant_root_a", actor="operator", root_id="other")
        budget = DispatchBudget(executor.base / "root_a" / "budget.json", scope="task_dispatch")
        first = budget.amend_limit(2.0, actor="operator", authority_id="raise_1",
                                   reason="more work", expected_generation=0)
        self.assertEqual(first, budget.amend_limit(2.0, actor="operator",
                         authority_id="raise_1", reason="more work", expected_generation=0))
        with self.assertRaises(BudgetError):
            budget.amend_limit(3.0, actor="operator", authority_id="raise_1",
                               reason="different", expected_generation=1)
        with self.assertRaises(BudgetError):
            DispatchBudget(budget.path, 1.0, scope="task_dispatch")
        self.assertEqual(2.0, budget.snapshot()["limit_usd"])

    def test_uncertainty_blocks_replay_and_retains_hold(self):
        adapter = IncompleteAdapter()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="grant_uncertain", actor="operator")
        first = executor.run(root)
        self.assertEqual("uncertain", first["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(1.0, first["budget"]["reserved_usd"])
        executor.run(root)
        self.assertEqual(1, len(adapter.calls))
        projection = legacy_attempt(first["attempts"][0], 1)
        self.assertEqual("interrupted", projection["execution_status"])
        self.assertEqual("unknown", projection["outcome"])
        reconciled = executor.reconcile_uncertain(root, actor="operator", reason="billing received",
                                                   cost_usd=0.12, evidence="provider:late-receipt",
                                                   writers_stopped=True)
        self.assertEqual("blocked", reconciled["state"])
        self.assertEqual(0.12, reconciled["budget"]["spent_usd"])
        self.assertEqual([], reconciled["budget"]["unresolved"])
        self.assertEqual(1, len(adapter.calls))

    def test_cancel_late_receipt_and_linked_continuation(self):
        adapter = CancellingAdapter()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="grant_cancel", actor="operator")
        adapter.executor, adapter.root = executor, root
        cancelled = executor.run(root)
        self.assertEqual("cancelled", cancelled["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(0.1, cancelled["budget"]["spent_usd"])
        self.assertEqual([], cancelled["budget"]["unresolved"])
        self.assertEqual("cancelled", executor.run(root)["state"])
        with self.assertRaises(ExecutorError):
            executor.continue_task(root, actor="", authority_id="bad", reason="retry")
        continued = executor.continue_task(root, actor="operator", authority_id="continue_1",
                                           reason="new authorised revision")
        self.assertEqual("ready", continued["state"])
        self.assertEqual(2, continued["revision"]["revision_number"])
        self.assertEqual("cancelled", continued["revision_history"][0]["terminal_state"])
        self.assertEqual(0.1, continued["budget"]["spent_usd"])

    def test_transition_graph_rejects_terminal_reopening(self):
        for source, edges in EDGES.items():
            for target in EDGES:
                value = {"state": source, "journal": []}
                if target in edges:
                    transition(value, target)
                    self.assertEqual(target, value["state"])
                else:
                    with self.assertRaises(ExecutorError):
                        transition(value, target)

    def test_adapter_requires_scoped_graft_without_paid_call(self):
        adapter = WorkerAdapter()
        with self.assertRaises(CapabilityError):
            adapter.capability(self.project)
        config = self.project / "mcp.json"
        config.write_text(json.dumps({"mcpServers": {"graft": {"command": sys.executable,
                            "args": ["graft", "mcp", "${CLAUDE_PROJECT_DIR:-.}"]}}}),
                          encoding="utf-8")
        adapter = WorkerAdapter(config)
        self.assertTrue(adapter.capability(self.project)["configured"])
        request = WorkerRequest(self.project, "Task", ("output.txt",),
                                "worker-sonnet-low", 0.5, "B0")
        with self.assertRaises(CapabilityError):
            adapter.command(request)
        admitted = WorkerRequest(self.project, "Task", ("output.txt",),
                                 "worker-sonnet-low", 0.5, "B0",
                                 admission_token="token", invocation_id="invocation",
                                 revision_id="revision", decision_digest="decision",
                                 intent_digest="intent")
        command = adapter.command(admitted)
        self.assertTrue(any(part.startswith("--mcp-config=") for part in command))
        self.assertIn("--restricted", command)
        self.assertNotIn("--safe-mode", command)
        self.assertTrue(any("mcp__graft__graft_find_code" in part for part in command))
        config.write_text(json.dumps({"mcpServers": {"other": {"command": "node", "args": []}}}),
                          encoding="utf-8")
        with self.assertRaises(CapabilityError):
            adapter.capability(self.project)

    def test_production_adapter_fake_stream_identity_and_timeout(self):
        config = self.project / "mcp.json"
        config.write_text(json.dumps({"mcpServers": {"graft": {"command": sys.executable,
                            "args": ["graft", "mcp", "${CLAUDE_PROJECT_DIR:-.}"]}}}),
                          encoding="utf-8")
        request = WorkerRequest(self.project, "Task", ("output.txt",),
                                "worker-sonnet-low", 0.5, "B0",
                                admission_token="token", invocation_id="invocation",
                                revision_id="revision", decision_digest="decision",
                                intent_digest="intent")
        def stream(model, child=False):
            rows = [{"type": "assistant", "parent_tool_use_id": "child" if child else None,
                     "message": {"model": model, "content": []}},
                    {"type": "result", "subtype": "success", "result": "done",
                     "total_cost_usd": 0.1, "usage": {"input_tokens": 10, "output_tokens": 4},
                     "modelUsage": {model: {"costUSD": 0.1}}}]
            return "\n".join(json.dumps(row) for row in rows) + "\n"
        good = WorkerAdapter(config, lambda cmd, cwd, env, timeout:
                             subprocess.CompletedProcess(cmd, 0, stream("claude-sonnet-5"), ""))
        result = good.run(request)
        self.assertEqual("completed", result["status"])
        self.assertEqual(0.1, result["cost_usd"])
        self.assertIsNone(result["served_effort"])
        self.assertEqual("cli-argument:low", result["effort_evidence"])
        wrong = WorkerAdapter(config, lambda cmd, cwd, env, timeout:
                              subprocess.CompletedProcess(cmd, 0, stream("claude-opus-5"), ""))
        self.assertEqual("failed", wrong.run(request)["status"])
        timed_out = WorkerAdapter(config, lambda cmd, cwd, env, timeout:
                                  (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd, timeout)))
        timeout_result = timed_out.run(request)
        self.assertEqual("interrupted", timeout_result["status"])
        self.assertIsNone(timeout_result["cost_usd"])

    def test_crash_before_reservation_recovers_without_double_call(self):
        executor, adapter = self.make()
        with patch.object(DispatchBudget, "reserve", side_effect=SystemExit("crash")):
            with self.assertRaises(SystemExit):
                executor.run("root_a")
        self.assertEqual(0, len(adapter.calls))
        state = executor.run("root_a")
        self.assertEqual("accepted", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(1, len(state["budget"]["invocations"]))

    def test_crash_after_reservation_settles_unused_hold(self):
        executor, adapter = self.make()
        original = DispatchBudget.reserve
        def reserve_then_crash(budget, *args, **kwargs):
            original(budget, *args, **kwargs)
            raise SystemExit("crash")
        with patch.object(DispatchBudget, "reserve", reserve_then_crash):
            with self.assertRaises(SystemExit):
                executor.run("root_a")
        state = executor.run("root_a")
        self.assertEqual("accepted", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(2, len(state["budget"]["invocations"]))
        self.assertEqual(0.1, state["budget"]["spent_usd"])
        self.assertEqual([], state["budget"]["unresolved"])

    def test_crash_after_start_refuses_relaunch(self):
        executor, adapter = self.make()
        original = DispatchBudget.start
        def start_then_crash(budget, *args, **kwargs):
            original(budget, *args, **kwargs)
            raise SystemExit("crash")
        with patch.object(DispatchBudget, "start", start_then_crash):
            with self.assertRaises(SystemExit):
                executor.run("root_a")
        state = executor.run("root_a")
        self.assertEqual("uncertain", state["state"])
        self.assertEqual(0, len(adapter.calls))
        self.assertEqual(1.0, state["budget"]["reserved_usd"])

    def test_crash_before_start_releases_hold_and_resumes_same_slot(self):
        executor, adapter = self.make()
        with patch.object(DispatchBudget, "start", side_effect=SystemExit("crash")):
            with self.assertRaises(SystemExit):
                executor.run("root_a")
        blocked = executor.run("root_a")
        self.assertEqual("blocked", blocked["state"])
        self.assertEqual(0, len(adapter.calls))
        self.assertEqual([], blocked["budget"]["unresolved"])
        executor.resume("root_a", actor="operator", reason="pre-dispatch evidence checked")
        done = executor.run("root_a")
        self.assertEqual("accepted", done["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(1, len(done["attempts"]))

    def test_crash_after_receipt_reconciles_without_relaunch(self):
        executor, adapter = self.make()
        with patch.object(DispatchBudget, "settle", side_effect=SystemExit("crash")):
            with self.assertRaises(SystemExit):
                executor.run("root_a")
        state = executor.run("root_a")
        self.assertEqual("accepted", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(0.1, state["budget"]["spent_usd"])

    def test_cancel_after_persisted_receipt_settles_without_relaunch(self):
        executor, adapter = self.make()
        with patch.object(DispatchBudget, "settle", side_effect=SystemExit("crash")):
            with self.assertRaises(SystemExit):
                executor.run("root_a")
        cancelled = executor.cancel("root_a", actor="operator", reason="stop after receipt")
        self.assertEqual("cancelled", cancelled["state"])
        self.assertEqual(0.1, cancelled["budget"]["spent_usd"])
        self.assertEqual([], cancelled["budget"]["unresolved"])
        self.assertEqual(1, len(adapter.calls))

    def test_crash_after_host_intent_has_no_replay(self):
        executor, adapter = self.make()
        with patch.object(executor, "record_receipt", side_effect=SystemExit("crash")):
            with self.assertRaises(SystemExit):
                executor.run("root_a")
        state = executor.run("root_a")
        self.assertEqual("uncertain", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(1.0, state["budget"]["reserved_usd"])

    def test_stale_callback_needs_explicit_reconciliation(self):
        class Stale(FakeAdapter):
            def run(self, request):
                receipt = super().run(request)
                self.executor.record_receipt(self.root, receipt, generation=0)
                return receipt
        adapter = Stale()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="stale_grant", actor="operator")
        adapter.executor, adapter.root = executor, root
        state = executor.run(root)
        self.assertEqual("uncertain", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertIsNone(state["attempts"][0]["receipt"])
        self.assertEqual(0.1, state["budget"]["spent_usd"])
        reconciled = executor.reconcile_uncertain(root, actor="operator", reason="late receipt inspected",
                                                   cost_usd=0.1, evidence="operator:verified-writer-stop",
                                                   writers_stopped=True)
        self.assertEqual("verifying", reconciled["state"])
        accepted = executor.run(root)
        self.assertEqual("accepted", accepted["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_duplicate_and_conflicting_receipt(self):
        executor, adapter = self.make()
        state = executor.run("root_a")
        receipt = state["attempts"][0]["receipt"]
        count = len(state["journal"])
        executor.record_receipt("root_a", receipt, generation=state["owner_generation"])
        self.assertEqual(count, len(executor.status("root_a")["journal"]))
        with self.assertRaises(ExecutorError):
            executor.record_receipt("root_a", {**receipt, "cost_usd": 0.2},
                                    generation=state["owner_generation"])
        latest = executor.status("root_a")
        self.assertEqual("accepted", latest["state"])
        self.assertEqual(0.1, latest["budget"]["spent_usd"])
        self.assertEqual("conflicting_receipt", latest["journal"][-1]["kind"])

    def test_rubric_review_and_stale_artefacts(self):
        self.contract.write_text(json.dumps({"version": 1, "kind": "rubric",
            "criteria": ["Looks correct"], "constraints": [], "required_outputs": ["output.txt"],
            "protected_paths": ["protected.txt"], "rubric": ["Review the output"],
            "timeout_s": 10}), encoding="utf-8")
        executor, adapter = self.make()
        pending = executor.run("root_a")
        self.assertEqual("awaiting_review", pending["state"])
        self.assertEqual(1, len(adapter.calls))
        (self.project / "output.txt").write_text("changed", encoding="utf-8")
        stale = executor.review("root_a", decision="pass", reviewer="operator")
        self.assertEqual("blocked", stale["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_two_processes_one_admission_and_one_host_call(self):
        script = r'''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from task_executor import TaskExecutor
class Fake:
    def capability(self, root):
        return {"configured": True, "actor_root": str(root.resolve()), "enforcement_proven": False}
    def run(self, request):
        (request.actor_root / ("call-" + request.invocation_id)).write_text("one", encoding="utf-8")
        (request.actor_root / "output.txt").write_text("accepted", encoding="utf-8")
        return {"admission_token": request.admission_token, "invocation_id": request.invocation_id,
                "revision_id": request.revision_id, "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest, "requested_cell": request.requested_cell,
                "actual_model": "claude-sonnet-5", "identity_valid": True, "child_models": [],
                "effort_evidence": "cli-argument:low",
                "terminal": True, "writer_stopped": True, "status": "completed", "cost_usd": 0.1,
                "usage": {"cost_usd": 0.1, "currency": "USD", "cost_source": "provider_reported"}}
project = Path(sys.argv[2])
executor = TaskExecutor(project, Fake())
try:
    executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                   acceptance_path=project / "acceptance.json", budget_usd=1,
                   authority_id="same_grant", actor="operator", root_id="same_root")
    print("WIN:" + executor.run("same_root")["state"])
except Exception as exc:
    print("CONFLICT:" + str(exc))
'''
        command = [sys.executable, "-I", "-c", script,
                   str(ROOT / "tools"), str(self.project)]
        first = subprocess.Popen(command, cwd=self.project, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(command, cwd=self.project, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
        outputs = [first.communicate(timeout=60), second.communicate(timeout=60)]
        self.assertEqual([0, 0], [first.returncode, second.returncode], outputs)
        lines = [out.strip() for out, _ in outputs]
        self.assertEqual(1, sum(line == "WIN:accepted" for line in lines), lines)
        self.assertEqual(1, sum(line.startswith("CONFLICT:") for line in lines), lines)
        self.assertEqual(1, len(list(self.project.glob("call-*"))))

    def test_frozen_inputs_and_definition_fail_closed(self):
        adapter = FakeAdapter()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="frozen_grant", actor="operator",
                              input_paths=["protected.txt"])
        (self.project / "protected.txt").write_text("changed", encoding="utf-8")
        blocked = executor.run(root)
        self.assertEqual("blocked", blocked["state"])
        self.assertEqual(0, len(adapter.calls))
        record = executor._path(root)
        value = json.loads(record.read_text(encoding="utf-8"))
        value["definition"]["goal"] = "different"
        record.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(ExecutorError):
            executor.status(root)

    def test_corrupt_frozen_acceptance_rejected_before_call(self):
        executor, adapter = self.make()
        path = executor._path("root_a")
        value = _read(path)
        value["definition"]["acceptance_definition"]["contract"]["criteria"] = ["changed"]
        value["definition_digest"] = digest(value["definition"])
        revision = value["revision"]
        revision["definition_digest"] = value["definition_digest"]
        revision["revision_id"] = digest({**{k: v for k, v in revision.items()
                                             if k != "revision_id"},
                                          "task_id": value["task_id"]})
        _write(path, value)
        with self.assertRaisesRegex(ExecutorError, "acceptance digest"):
            executor.run("root_a")
        self.assertEqual(0, len(adapter.calls))

    def test_post_dispatch_identity_fault_is_not_quality_repair(self):
        class WrongModel(FakeAdapter):
            def run(self, request):
                result = super().run(request)
                result["actual_model"] = "claude-opus-5"
                return result
        adapter = WrongModel()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="identity_grant", actor="operator")
        state = executor.run(root)
        self.assertEqual("blocked", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(0.1, state["budget"]["spent_usd"])
        with self.assertRaises(ExecutorError):
            executor.resume(root, actor="operator", reason="try again")
        self.assertEqual(1, len(adapter.calls))

    def test_protected_tamper_blocks_and_partial_is_distinct(self):
        class Tamper(FakeAdapter):
            def run(self, request):
                result = super().run(request)
                (request.actor_root / "protected.txt").write_text("tampered", encoding="utf-8")
                return result
        adapter = Tamper()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="tamper_grant", actor="operator")
        blocked = executor.run(root)
        self.assertEqual("blocked", blocked["state"])
        self.assertEqual(1, len(adapter.calls))
        partial = executor.finalise_partial(root, actor="operator", reason="useful output; boundary failed")
        self.assertEqual("partial", partial["state"])
        self.assertEqual(0.1, partial["budget"]["spent_usd"])
        self.assertEqual("partial", executor.run(root)["state"])

    def test_verifier_resume_never_launches_another_worker(self):
        executor, adapter = self.make()
        with patch("task_executor.acceptance.verify", side_effect=RuntimeError("verifier unavailable")):
            blocked = executor.run("root_a")
        self.assertEqual("blocked", blocked["state"])
        self.assertEqual("verifying", blocked["block"]["resume_phase"])
        self.assertEqual(1, len(adapter.calls))
        executor.resume("root_a", actor="operator", reason="verifier restored")
        done = executor.run("root_a")
        self.assertEqual("accepted", done["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_predispatch_capability_block_resumes_unused_slot(self):
        class Toggle(FakeAdapter):
            def __init__(self):
                super().__init__()
                self.available = True
            def capability(self, root):
                if not self.available:
                    raise CapabilityError("Graft MCP unavailable")
                return super().capability(root)
        adapter = Toggle()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="capability_grant", actor="operator")
        adapter.available = False
        blocked = executor.run(root)
        self.assertEqual("blocked", blocked["state"])
        self.assertIn("Graft MCP unavailable", blocked["block"]["reason"])
        self.assertEqual(0, len(adapter.calls))
        adapter.available = True
        executor.resume(root, actor="operator", reason="Graft restored")
        done = executor.run(root)
        self.assertEqual("accepted", done["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_cancellation_during_external_verifier_discards_stale_result(self):
        executor, adapter = self.make()
        import acceptance as acceptance_module
        original = acceptance_module.verify
        def cancel_during_verify(project, contract, entry_id):
            result = original(project, contract, entry_id)
            executor.cancel("root_a", actor="operator", reason="stop during verification")
            return result
        with patch("task_executor.acceptance.verify", cancel_during_verify):
            state = executor.run("root_a")
        self.assertEqual("cancelled", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertTrue(any(event["kind"] == "late_verification" for event in state["journal"]))

    def test_b0_failure_path_never_calls_controller_decision(self):
        executor, adapter = self.make(fail_count=3)
        with patch("task_executor.route.controller_decision", side_effect=AssertionError("Controller invoked")):
            state = executor.run("root_a")
        self.assertEqual("failed", state["state"])
        self.assertEqual(3, len(adapter.calls))

    def test_inclusive_billing_sample_is_one_root_charge(self):
        class Inclusive(FakeAdapter):
            def run(self, request):
                receipt = super().run(request)
                receipt["billed_models"] = ["claude-sonnet-5", "auxiliary-provider-model"]
                receipt["usage"]["includes_descendants"] = True
                return receipt
        adapter = Inclusive()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="inclusive_grant", actor="operator")
        done = executor.run(root)
        self.assertEqual("accepted", done["state"])
        self.assertEqual(0.1, done["budget"]["spent_usd"])
        self.assertEqual(0.1, legacy_attempt(done["attempts"][0], 1)["usage"]["cost_usd"])

    def test_child_model_receipt_is_blocked(self):
        class Child(FakeAdapter):
            def run(self, request):
                receipt = super().run(request)
                receipt["child_models"] = ["claude-sonnet-5"]
                return receipt
        adapter = Child()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="child_grant", actor="operator")
        state = executor.run(root)
        self.assertEqual("blocked", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(0.1, state["budget"]["spent_usd"])

    def test_rubric_review_pass_does_not_call_worker(self):
        self.contract.write_text(json.dumps({"version": 1, "kind": "rubric",
            "criteria": ["Looks correct"], "required_outputs": ["output.txt"],
            "protected_paths": ["protected.txt"], "rubric": ["Review output"]}),
            encoding="utf-8")
        executor, adapter = self.make()
        pending = executor.run("root_a")
        self.assertEqual("awaiting_review", pending["state"])
        passed = executor.review("root_a", decision="pass", reviewer="operator")
        self.assertEqual("accepted", passed["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_rubric_review_fail_uses_same_revision_and_next_slot(self):
        self.contract.write_text(json.dumps({"version": 1, "kind": "rubric",
            "criteria": ["Looks correct"], "required_outputs": ["output.txt"],
            "protected_paths": ["protected.txt"], "rubric": ["Review output"]}),
            encoding="utf-8")
        executor, adapter = self.make()
        pending = executor.run("root_a")
        definition_digest = pending["definition_digest"]
        failed = executor.review("root_a", decision="fail", reviewer="operator")
        self.assertEqual("ready", failed["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertEqual(definition_digest, failed["definition_digest"])
        next_review = executor.run("root_a")
        self.assertEqual("awaiting_review", next_review["state"])
        self.assertEqual(2, len(adapter.calls))
        self.assertEqual(definition_digest, next_review["definition_digest"])
        passed = executor.review("root_a", decision="pass", reviewer="operator")
        self.assertEqual("accepted", passed["state"])

    def test_overlap_and_corrupt_budget_fail_closed(self):
        executor, adapter = self.make()
        with self.assertRaises(ExecutorError):
            executor.admit(goal="Other", scope=["output.txt"], permissions=["read", "edit"],
                           acceptance_path=self.contract, budget_usd=2,
                           authority_id="different_grant", actor="operator", root_id="other_root")
        path = executor.base / "root_a" / "budget.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["limit_units"] += 1
        path.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(BudgetError):
            executor.run("root_a")
        self.assertEqual(0, len(adapter.calls))

    def test_missing_effort_evidence_blocks_without_repair(self):
        class NoEffort(FakeAdapter):
            def run(self, request):
                receipt = super().run(request)
                receipt.pop("effort_evidence")
                return receipt
        adapter = NoEffort()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="no_effort_grant", actor="operator")
        blocked = executor.run(root)
        self.assertEqual("blocked", blocked["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_unmatched_admission_token_never_completes_task(self):
        class WrongToken(FakeAdapter):
            def run(self, request):
                receipt = super().run(request)
                receipt["admission_token"] = "stale-token"
                return receipt
        adapter = WrongToken()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="wrong_token_grant", actor="operator")
        state = executor.run(root)
        self.assertEqual("blocked", state["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertIsNone(state["attempts"][0]["receipt"])
        self.assertEqual(1.0, state["budget"]["reserved_usd"])
        self.assertTrue(any(event["kind"] == "unmatched_receipt" for event in state["journal"]))

    def test_first_failed_output_preserved_across_repair(self):
        class WrongThenRight(FakeAdapter):
            def run(self, request):
                result = super().run(request)
                if len(self.calls) == 1:
                    (request.actor_root / "output.txt").write_text("wrong", encoding="utf-8")
                return result
        adapter = WrongThenRight()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="snapshot_grant", actor="operator")
        result = executor.run(root)
        self.assertEqual("accepted", result["state"])
        self.assertEqual(2, len(adapter.calls))
        first = result["attempts"][0]
        saved = self.project / first["artefact_snapshot"]["files"][0]["path"]
        self.assertEqual("wrong", saved.read_text(encoding="utf-8"))
        self.assertEqual("accepted", (self.project / "output.txt").read_text(encoding="utf-8"))

    def test_rollback_audit_blocks_open_or_unsettled_roots(self):
        executor, _ = self.make()
        self.assertFalse(audit(self.project)["rollback_safe"])
        self.assertEqual("accepted", executor.run("root_a")["state"])
        self.assertTrue(audit(self.project)["rollback_safe"])

    def test_cancel_from_each_nonterminal_state_requires_authority(self):
        executor, _ = self.make()
        path = executor._path("root_a")
        for state in EDGES:
            if state in ("accepted", "failed", "partial", "cancelled"):
                continue
            with self.subTest(state=state):
                fixture = _read(path)
                fixture["state"] = state
                _write(path, fixture)
                with self.assertRaises(ExecutorError):
                    executor.cancel("root_a", actor="", reason="")
                self.assertEqual("cancelled", executor.cancel(
                    "root_a", actor="operator", reason="stop")["state"])

    def test_override_is_unsupported_and_definition_stays_stable(self):
        executor, _ = self.make()
        before = executor.status("root_a")
        with self.assertRaisesRegex(ExecutorError, "unsupported in N1"):
            executor.override_cell("root_a", cell="worker-opus-max",
                                   actor="operator", reason="manual request")
        after = executor.status("root_a")
        self.assertEqual(before["definition_digest"], after["definition_digest"])
        self.assertEqual(before["revision"], after["revision"])

    def test_deadline_before_dispatch_and_during_active_writer(self):
        past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
        adapter = FakeAdapter()
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=1,
                              authority_id="deadline_before", actor="operator",
                              root_id="deadline_before", deadline_at=past)
        self.assertEqual("cancelled", executor.run(root)["state"])
        self.assertEqual(0, len(adapter.calls))
        class Slow(FakeAdapter):
            def __init__(self):
                super().__init__()
                self.signals = []
            def run(self, request):
                time.sleep(2.2)
                return super().run(request)
            def cancel(self, invocation_id):
                self.signals.append(invocation_id)
        slow = Slow()
        second_project = self.project / "second-project"
        second_project.mkdir()
        (second_project / "protected.txt").write_text("fixed", encoding="utf-8")
        second_contract = second_project / "acceptance.json"
        second_contract.write_bytes(self.contract.read_bytes())
        running = TaskExecutor(second_project, slow)
        soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=2)).isoformat()
        second = running.admit(goal="Task", scope=["output.txt"], permissions=["read", "edit"],
                               acceptance_path=second_contract, budget_usd=1,
                               authority_id="deadline_during", actor="operator",
                               root_id="deadline_during", deadline_at=soon)
        stopped = running.run(second)
        self.assertEqual("cancelled", stopped["state"])
        self.assertEqual(1, len(slow.calls))
        self.assertEqual(1, len(slow.signals))
        self.assertEqual(0.1, stopped["budget"]["spent_usd"])


if __name__ == "__main__":
    unittest.main()
