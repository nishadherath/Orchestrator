#!/usr/bin/env python3
"""N2 managed child DAG checks; all worker calls use an observable fake."""
from __future__ import annotations

import copy
import datetime as dt
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import managed_delegation  # noqa: E402
from managed_delegation import DelegationError, ManagedDelegation  # noqa: E402
from task_executor import TaskExecutor, ExecutorError, _read, _write, audit  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402
from route import ledger_lock, LedgerLockTimeout  # noqa: E402
from worker_adapter import WorkerAdapter, digest  # noqa: E402


class ChildAdapter:
    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()
        self.started = threading.Event()
        self.release = threading.Event()
        self.wait = False
        self.cancelled = []
        self.bad_identity = False
        self.unknown_cost = False
        self.barrier = None
        self.child_model = False

    def capability(self, root):
        return {"configured": True, "graft_only": True,
                "actor_root": str(root.resolve()),
                "managed_delegation_enforced": True,
                "cancellation_supported": True,
                "max_child_depth": 3, "max_child_concurrency": 2,
                "enforcement_proven": True}

    def cancel(self, invocation_id):
        self.cancelled.append(invocation_id)
        self.release.set()
        return True

    def run(self, request):
        with self.lock:
            self.calls.append(request)
        self.started.set()
        if self.barrier is not None:
            self.barrier.wait(timeout=3)
        if self.wait:
            if not self.release.wait(5):
                raise RuntimeError("test adapter never released")
        for output in request.allowed_edits:
            (request.actor_root / output).write_text("accepted", encoding="utf-8")
        model = "claude-sonnet-5" if "sonnet" in request.requested_cell else "claude-opus-5"
        effort = request.requested_cell.split("-")[-1]
        cost = None if self.unknown_cost else 0.1
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": "wrong-model" if self.bad_identity else model,
                "identity_valid": not self.bad_identity,
                "child_models": ["claude-opus-5"] if self.child_model else [],
                "status": "completed", "terminal": cost is not None,
                "writer_stopped": cost is not None, "cost_usd": cost,
                "usage": {"cost_usd": cost, "cost_source": "provider_reported"},
                "effort_evidence": f"cli-argument:{effort}",
                "started_at": "2026-09-24T00:00:00Z",
                "finished_at": "2026-09-24T00:00:01Z", "wall_clock_s": 1.0}


class DelegationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="worker-n2-")
        self.addCleanup(tmp.cleanup)
        self.project = Path(tmp.name)
        (self.project / "protected.txt").write_text("fixed", encoding="utf-8")
        (self.project / "input.txt").write_text("public", encoding="utf-8")
        self.adapter = ChildAdapter()
        self.executor = TaskExecutor(self.project, self.adapter)
        self.root_id = self.executor.admit(
            goal="root", scope=["a.txt", "b.txt", "c.txt", "final.txt"],
            permissions=["read", "edit"], acceptance_path=self.contract("final.txt"),
            budget_usd=2.0, authority_id="grant_root", actor="operator",
            root_id="root_n2", input_paths=["input.txt"])
        self.manager = ManagedDelegation(self.executor)

    def contract(self, output, kind="command"):
        path = self.project / f"accept-{output}.json"
        path.write_text(json.dumps({"version": 1, "kind": kind,
            "criteria": ["accepted output"], "required_outputs": [output],
            "protected_paths": ["protected.txt"],
            "command": ([sys.executable, "-c",
                f"from pathlib import Path; import sys; sys.exit(0 if Path('{output}').read_text() == 'accepted' else 1)"]
                if kind == "command" else []),
            "rubric": ["output is correct"] if kind == "rubric" else [],
            "timeout_s": 10}), encoding="utf-8")
        return path

    def item(self, ident, output, *, parent=None, deps=None, envelope=0.2):
        return {"id": ident, "parent_id": parent, "depends_on": deps or [],
                "goal": f"child {ident}", "reads": ["input.txt"],
                "writes": [output], "permissions": ["read", "edit"],
                "acceptance_path": self.contract(output).name,
                "requested_cell": "worker-sonnet-low", "allowance_usd": 0.2,
                "envelope_usd": envelope, "deadline_at": None,
                "return_contract": "verified_acceptance"}

    def plan(self, items, concurrency=1, depth=1):
        return {"version": 1, "items": items, "max_depth": depth,
                "max_concurrency": concurrency, "parent_reserve_usd": 0.3,
                "parallel_reason": "independent disjoint outputs reduce latency" if concurrency > 1 else ""}

    def test_independent_children_then_root_b0_no_double_charge(self):
        proposal = self.plan([self.item("a", "a.txt"), self.item("b", "b.txt")], concurrency=2)
        self.manager.admit(self.root_id, proposal, actor="operator", authority_id="plan_1")
        with self.assertRaises(ExecutorError):
            self.executor.run(self.root_id)
        result = self.manager.run(self.root_id)
        self.assertEqual("complete", result["delegation"]["state"])
        self.assertEqual(2, len(self.adapter.calls))
        self.assertEqual({"accepted"}, {c["state"] for c in result["delegation"]["children"].values()})
        self.assertAlmostEqual(0.2, result["budget"]["spent_usd"])
        self.assertEqual([], result["budget"]["unresolved"])
        self.assertEqual(2, len(result["budget"]["invocations"]))
        self.assertEqual("accepted", self.executor.run(self.root_id)["state"])
        self.assertAlmostEqual(0.3, self.executor.status(self.root_id)["budget"]["spent_usd"])
        self.assertTrue(audit(self.project)["rollback_safe"])

    def test_nested_envelope_dependencies_and_one_call_per_node(self):
        proposal = self.plan([self.item("parent", "a.txt", envelope=0.4),
                              self.item("nested", "c.txt", parent="parent", deps=["parent"])], depth=2)
        self.manager.admit(self.root_id, proposal, actor="operator", authority_id="plan_2")
        result = self.manager.run(self.root_id)
        self.assertEqual("complete", result["delegation"]["state"])
        self.assertEqual(["child parent", "child nested"], [call.issue for call in self.adapter.calls])
        self.assertAlmostEqual(0.2, result["budget"]["spent_usd"])

    def test_independent_children_actually_overlap(self):
        self.adapter.barrier = threading.Barrier(2)
        proposal = self.plan([self.item("a", "a.txt"), self.item("b", "b.txt")], concurrency=2)
        self.manager.admit(self.root_id, proposal, actor="operator", authority_id="plan_1")
        self.assertEqual("complete", self.manager.run(self.root_id)["delegation"]["state"])
        self.assertEqual(2, len(self.adapter.calls))

    def test_graph_and_authority_rejections_before_any_child_call(self):
        base = self.plan([self.item("a", "a.txt"), self.item("b", "b.txt")])
        variants = []
        cycle = copy.deepcopy(base)
        cycle["items"][0]["depends_on"] = ["b"]
        cycle["items"][1]["depends_on"] = ["a"]
        variants.append(cycle)
        parent_cycle = copy.deepcopy(base)
        parent_cycle["items"][0]["parent_id"] = "b"
        parent_cycle["items"][1]["parent_id"] = "a"
        variants.append(parent_cycle)
        conflict = copy.deepcopy(base)
        conflict["items"][1]["writes"] = ["a.txt"]
        variants.append(conflict)
        outside = copy.deepcopy(base)
        outside["items"][1]["writes"] = ["../escape.txt"]
        variants.append(outside)
        too_deep = copy.deepcopy(base)
        too_deep["items"][1]["parent_id"] = "a"
        variants.append(too_deep)
        unordered_nested = copy.deepcopy(base)
        unordered_nested["max_depth"] = 2
        unordered_nested["items"][0]["envelope_usd"] = 0.4
        unordered_nested["items"][1]["parent_id"] = "a"
        variants.append(unordered_nested)
        oversub = copy.deepcopy(base)
        oversub["items"][0]["envelope_usd"] = 1.9
        variants.append(oversub)
        bad_cap = copy.deepcopy(base)
        bad_cap["max_concurrency"] = 3
        variants.append(bad_cap)
        for proposal in variants:
            with self.subTest(proposal=proposal):
                with self.assertRaises((DelegationError, ValueError)):
                    self.manager.admit(self.root_id, proposal, actor="operator", authority_id="plan_bad")
                self.assertNotIn("delegation", self.executor.status(self.root_id))
        self.assertEqual([], self.adapter.calls)

    def test_nested_parent_cap_is_enforced(self):
        proposal = self.plan([self.item("p", "a.txt", envelope=0.2),
                              self.item("c", "c.txt", parent="p", deps=["p"])], depth=2)
        with self.assertRaisesRegex(DelegationError, "envelope"):
            self.manager.admit(self.root_id, proposal, actor="operator", authority_id="plan_1")

    def test_real_adapter_reports_unenforced_boundary(self):
        with patch.object(WorkerAdapter, "capability", return_value={
                "graft_only": True, "managed_delegation_enforced": False,
                "cancellation_supported": True, "max_child_depth": 0,
                "max_child_concurrency": 0}):
            self.executor.adapter = WorkerAdapter()
            with self.assertRaisesRegex(DelegationError, "cannot enforce"):
                self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                                   actor="operator", authority_id="plan_1")
        self.assertEqual([], self.executor.status(self.root_id)["budget"]["unresolved"])

    def test_quality_failure_blocks_dependency_and_releases_unused_hold(self):
        proposal = self.plan([self.item("a", "a.txt"),
                              self.item("b", "b.txt", deps=["a"])])
        self.manager.admit(self.root_id, proposal, actor="operator", authority_id="plan_1")
        original = self.adapter.run
        def wrong_output(request):
            result = original(request)
            if request.issue == "child a":
                (request.actor_root / "a.txt").write_text("wrong", encoding="utf-8")
            return result
        self.adapter.run = wrong_output
        result = self.manager.run(self.root_id)
        self.assertEqual("blocked", result["state"])
        self.assertEqual("failed", result["delegation"]["children"]["a"]["state"])
        self.assertEqual("dependency_blocked", result["delegation"]["children"]["b"]["state"])
        self.assertEqual(1, len(self.adapter.calls))
        self.assertEqual([], result["budget"]["unresolved"])
        self.assertEqual("partial", self.executor.finalise_partial(self.root_id,
            actor="operator", reason="useful incomplete output")["state"])

    def test_cancellation_signals_child_and_late_charge_is_counted_once(self):
        self.adapter.wait = True
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                           actor="operator", authority_id="plan_1")
        thread = threading.Thread(target=lambda: self.manager.run(self.root_id))
        thread.start()
        self.assertTrue(self.adapter.started.wait(3))
        cancelled = self.executor.cancel(self.root_id, actor="operator", reason="stop")
        self.assertEqual("cancelled", cancelled["state"])
        self.assertEqual(1, len(cancelled["budget"]["unresolved"]))
        thread.join(5)
        self.assertFalse(thread.is_alive())
        final = self.executor.status(self.root_id)
        self.assertEqual("cancelled", final["state"])
        self.assertEqual([], final["budget"]["unresolved"])
        self.assertAlmostEqual(0.1, final["budget"]["spent_usd"])
        self.assertEqual(1, len(self.adapter.calls))
        self.assertEqual(1, len(self.adapter.cancelled))

    def test_started_without_intent_is_uncertain_without_replay(self):
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                           actor="operator", authority_id="plan_1")
        original_write = managed_delegation._write
        def crash_on_intent(path, value):
            if value["delegation"]["children"]["a"]["state"] == "running":
                raise OSError("injected crash after budget.start")
            return original_write(path, value)
        with patch.object(managed_delegation, "_write", side_effect=crash_on_intent):
            with self.assertRaises(OSError):
                self.manager.run(self.root_id)
        recovered = ManagedDelegation(self.executor).run(self.root_id)
        self.assertEqual("blocked", recovered["state"])
        self.assertEqual("uncertain", recovered["delegation"]["children"]["a"]["state"])
        self.assertEqual(1, len(recovered["budget"]["unresolved"]))
        self.assertEqual([], self.adapter.calls)
        resolved = self.manager.reconcile_child(self.root_id, "a", actor="operator",
            evidence="provider-bill-1", cost_usd=0.07, writers_stopped=True)
        self.assertEqual([], resolved["budget"]["unresolved"])
        self.assertAlmostEqual(0.07, resolved["budget"]["spent_usd"])

    def test_unknown_cost_retains_hold_and_no_dependent_call(self):
        self.adapter.unknown_cost = True
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt"),
            self.item("b", "b.txt", deps=["a"])]), actor="operator", authority_id="plan_1")
        result = self.manager.run(self.root_id)
        self.assertEqual("blocked", result["state"])
        self.assertEqual("uncertain", result["delegation"]["children"]["a"]["state"])
        self.assertEqual(1, len(result["budget"]["unresolved"]))
        self.assertEqual(1, len(self.adapter.calls))

    def test_expired_child_deadline_cancels_root_without_call(self):
        item = self.item("a", "a.txt")
        item["deadline_at"] = (dt.datetime.now(dt.timezone.utc)
                               - dt.timedelta(seconds=1)).isoformat()
        self.manager.admit(self.root_id, self.plan([item]),
                           actor="operator", authority_id="plan_1")
        result = self.manager.run(self.root_id)
        self.assertEqual("cancelled", result["state"])
        self.assertEqual([], result["budget"]["unresolved"])
        self.assertEqual([], self.adapter.calls)

    def test_pre_start_crash_releases_unused_id_then_dispatches_once(self):
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                           actor="operator", authority_id="plan_1")
        original_start = DispatchBudget.start
        raised = False
        def crash_once(budget, invocation_id):
            nonlocal raised
            if not raised:
                raised = True
                raise OSError("injected crash before budget start")
            return original_start(budget, invocation_id)
        with patch.object(DispatchBudget, "start", crash_once):
            with self.assertRaises(OSError):
                self.manager.run(self.root_id)
        recovered = ManagedDelegation(self.executor).run(self.root_id)
        self.assertEqual("complete", recovered["delegation"]["state"])
        self.assertEqual(1, len(self.adapter.calls))
        self.assertEqual(2, len(recovered["budget"]["invocations"]))
        self.assertAlmostEqual(0.1, recovered["budget"]["spent_usd"])

    def test_persisted_receipt_recovery_verifies_without_replay(self):
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                           actor="operator", authority_id="plan_1")
        request = self.manager._prepare(self.root_id, "a")
        receipt = self.adapter.run(request)
        path = self.executor._path(self.root_id)
        with ledger_lock(path):
            root = _read(path)
            child = root["delegation"]["children"]["a"]
            child["receipt"] = receipt
            child["receipt_digest"] = digest(receipt)
            _write(path, root)
        result = ManagedDelegation(self.executor).run(self.root_id)
        self.assertEqual("complete", result["delegation"]["state"])
        self.assertEqual(1, len(self.adapter.calls))
        self.assertAlmostEqual(0.1, result["budget"]["spent_usd"])

    def test_parallel_runner_has_single_owner(self):
        self.adapter.wait = True
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                           actor="operator", authority_id="plan_1")
        thread = threading.Thread(target=lambda: self.manager.run(self.root_id))
        thread.start()
        self.assertTrue(self.adapter.started.wait(3))
        with self.assertRaises(LedgerLockTimeout):
            ManagedDelegation(self.executor).run(self.root_id)
        self.adapter.release.set()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(1, len(self.adapter.calls))

    def test_identity_fault_charges_once_and_stops_graph(self):
        self.adapter.bad_identity = True
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt"),
            self.item("b", "b.txt", deps=["a"])]), actor="operator", authority_id="plan_1")
        result = self.manager.run(self.root_id)
        self.assertEqual("blocked", result["state"])
        self.assertEqual("blocked", result["delegation"]["children"]["a"]["state"])
        self.assertEqual(1, len(self.adapter.calls))
        self.assertEqual([], result["budget"]["unresolved"])
        self.assertAlmostEqual(0.1, result["budget"]["spent_usd"])

    def test_unmanaged_child_model_is_rejected(self):
        self.adapter.child_model = True
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                           actor="operator", authority_id="plan_1")
        result = self.manager.run(self.root_id)
        self.assertEqual("blocked", result["state"])
        self.assertEqual(1, len(self.adapter.calls))

    def test_root_cannot_accept_after_required_child_output_changes(self):
        self.manager.admit(self.root_id, self.plan([self.item("a", "a.txt")]),
                           actor="operator", authority_id="plan_1")
        self.assertEqual("complete", self.manager.run(self.root_id)["delegation"]["state"])
        original = self.adapter.run
        def change_child_after_call(request):
            receipt = original(request)
            if request.issue == "root":
                (request.actor_root / "a.txt").write_text("changed", encoding="utf-8")
            return receipt
        self.adapter.run = change_child_after_call
        result = self.executor.run(self.root_id)
        self.assertEqual("blocked", result["state"])
        self.assertIn("required child output changed", result["block"]["reason"])

    def test_review_child_and_resume_dependent(self):
        item = self.item("a", "a.txt")
        item["acceptance_path"] = self.contract("a.txt", kind="rubric").name
        self.manager.admit(self.root_id, self.plan([item, self.item("b", "b.txt", deps=["a"])]),
                           actor="operator", authority_id="plan_1")
        pending = self.manager.run(self.root_id)
        self.assertEqual("awaiting_review", pending["delegation"]["children"]["a"]["state"])
        self.assertEqual(1, len(self.adapter.calls))
        self.manager.review_child(self.root_id, "a", decision="pass", reviewer="operator")
        done = self.manager.run(self.root_id)
        self.assertEqual("complete", done["delegation"]["state"])
        self.assertEqual(2, len(self.adapter.calls))


if __name__ == "__main__":
    unittest.main()
