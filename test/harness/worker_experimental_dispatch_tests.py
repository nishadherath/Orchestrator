#!/usr/bin/env python3
"""Provider-free proof that N5 experimental arms actually dispatch their cells."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import model_registry  # noqa: E402
import worker_selector  # noqa: E402
from task_executor import TaskExecutor, ExecutorError, _read, _write  # noqa: E402


class FakeAdapter:
    offline_fake = True

    def __init__(self, failures: int = 0, incomplete: bool = False):
        self.failures = failures
        self.incomplete = incomplete
        self.calls = []

    def capability(self, root):
        return {"actor_root": str(root.resolve()), "enforcement_proven": False,
                "budget_enforced": True,
                "supported_cells": sorted(model_registry.load()["cells"])}

    def run(self, request):
        self.calls.append(request)
        cell = model_registry.resolve_cell(request.requested_cell)
        if len(self.calls) > self.failures:
            (request.actor_root / "output.txt").write_text("accepted", encoding="utf-8")
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": cell["expected_provider_model"],
                "identity_valid": True, "child_models": [],
                "status": "interrupted" if self.incomplete else "completed",
                "terminal": not self.incomplete, "writer_stopped": not self.incomplete,
                "cost_usd": None if self.incomplete else 0.1,
                "usage": {"cost_usd": None if self.incomplete else 0.1},
                "effort_evidence": f"cli-argument:{cell['effort']}",
                "started_at": "2026-09-25T00:00:00Z",
                "finished_at": "2026-09-25T00:00:01Z", "wall_clock_s": 1.0}


def assessment(complexity="moderate"):
    return worker_selector.assess({
        "task_kind": "implementation", "complexity": complexity,
        "verification": "executable", "context_tokens": 2500,
        "deadline_seconds": None, "failure_cause": "none",
        "prior_local_repairs": 0, "frame_confidence": "clear",
        "required_artefacts": ["output.txt"],
        "evidence": [{"source": "operator", "reference": "task",
                      "claim": "produce accepted output"}]})


def dispatch(arm="candidate", complexity="moderate", alternative_cell="worker-sonnet-xhigh"):
    return {"schema_version": 1, "arm": arm,
            "manifest_sha256": "a" * 64, "assessment": assessment(complexity),
            "alternative_cell": alternative_cell if arm == "alternative" else None,
            "fallback_cell": "worker-opus-high", "cost_ceiling_usd": 3.0}


def dispatch_v2(first_cell="worker-sonnet-xhigh", complexity="moderate"):
    return {"schema_version": 2, "arm": "alternative",
            "manifest_sha256": "b" * 64, "assessment": assessment(complexity),
            "alternative_cell": first_cell,
            "repair_cells": ["worker-sonnet-low", "worker-opus-high"],
            "cost_ceiling_usd": 3.0}


class ExperimentalDispatchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="worker-n5-dispatch-")
        self.addCleanup(temp.cleanup)
        self.project = Path(temp.name)
        (self.project / "protected.txt").write_text("fixed", encoding="utf-8")
        self.contract = self.project / "acceptance.json"
        self.contract.write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["output accepted"],
            "constraints": [], "required_outputs": ["output.txt"],
            "protected_paths": ["protected.txt"],
            "command": [sys.executable, "-c",
                        "from pathlib import Path; import sys; sys.exit(0 if Path('output.txt').read_text() == 'accepted' else 1)"],
            "timeout_s": 10}), encoding="utf-8")

    def admit(self, adapter, spec, suffix=""):
        executor = TaskExecutor(self.project, adapter)
        root = executor.admit(goal="Create accepted output", scope=["output.txt"],
                              permissions=["read", "edit"],
                              acceptance_path=self.contract, budget_usd=3.0,
                              authority_id="grant" + suffix, actor="operator",
                              root_id="root" + suffix,
                              experimental_dispatch=spec)
        return executor, root

    def test_candidate_dispatches_selected_cell_and_freezes_decisions(self):
        adapter = FakeAdapter(failures=1)
        executor, root = self.admit(adapter, dispatch())
        result = executor.run(root)
        self.assertEqual("accepted", result["state"])
        self.assertEqual(["worker-sonnet-high"] * 2,
                         [call.requested_cell for call in adapter.calls])
        self.assertEqual("N5-experimental-v1", result["admission"]["policy"])
        self.assertEqual("worker-sonnet-high", result["experimental_policy"]["selected_cell"])
        decisions = [event["data"]["decision"] for event in result["journal"]
                     if event["kind"] == "decision"]
        self.assertEqual(2, len(decisions))
        for row in decisions:
            self.assertEqual("candidate", row["arm"])
            self.assertEqual(result["admission"]["policy_digest"], row["policy_digest"])
            self.assertEqual("a" * 64, row["manifest_sha256"])
            self.assertEqual(3.0, row["cost_ceiling_usd"])
            self.assertIn(row["cell"], row["eligible_cells"])

    def test_alternative_is_an_executed_arm(self):
        adapter = FakeAdapter()
        executor, root = self.admit(adapter, dispatch("alternative"))
        result = executor.run(root)
        self.assertEqual("accepted", result["state"])
        self.assertEqual("worker-sonnet-xhigh", adapter.calls[0].requested_cell)
        self.assertEqual("alternative", result["experimental_policy"]["arm"])

    def test_explicitly_capped_fable_comparison_when_cost_projection_unknown(self):
        adapter = FakeAdapter()
        executor, root = self.admit(adapter, dispatch(
            "alternative", "complex", "worker-fable-high"))
        result = executor.run(root)
        self.assertEqual("accepted", result["state"])
        self.assertEqual("worker-fable-high", adapter.calls[0].requested_cell)
        self.assertEqual(3.0, result["experimental_policy"]["cost_ceiling_usd"])

    def test_q4_changes_only_first_cell_and_freezes_common_tail(self):
        for number, first in enumerate(("worker-sonnet-xhigh", "worker-opus-high"), 1):
            with self.subTest(first=first):
                (self.project / "output.txt").unlink(missing_ok=True)
                adapter = FakeAdapter(failures=2)
                executor, root = self.admit(adapter, dispatch_v2(first), str(number))
                result = executor.run(root)
                self.assertEqual("accepted", result["state"])
                self.assertEqual([first, "worker-sonnet-low", "worker-opus-high"],
                                 [call.requested_cell for call in adapter.calls])
                self.assertEqual("Q4-first-cell-v2", result["admission"]["policy"])
                self.assertEqual(["worker-sonnet-low", "worker-opus-high"],
                                 result["experimental_policy"]["common_repair_tail"])
                decisions = [event["data"]["decision"] for event in result["journal"]
                             if event["kind"] == "decision"]
                self.assertEqual([1, 2, 3], [row["sequence"] for row in decisions])
                self.assertTrue(all(row["policy"] == "Q4-first-cell-v2"
                                    for row in decisions))

    def test_q4_rejects_changed_tail_before_dispatch(self):
        for repairs in (["worker-opus-high", "worker-sonnet-low"],
                        ["worker-sonnet-low", "worker-sonnet-low"],
                        ["worker-sonnet-high", "worker-opus-high"]):
            with self.subTest(repairs=repairs):
                adapter = FakeAdapter()
                with self.assertRaises(ExecutorError):
                    self.admit(adapter, {**dispatch_v2(), "repair_cells": repairs})
                self.assertEqual([], adapter.calls)

    def test_uncertain_call_is_not_replayed(self):
        adapter = FakeAdapter(incomplete=True)
        executor, root = self.admit(adapter, dispatch())
        self.assertEqual("uncertain", executor.run(root)["state"])
        self.assertEqual("uncertain", executor.run(root)["state"])
        self.assertEqual(1, len(adapter.calls))
        self.assertGreater(executor.status(root)["budget"]["reserved_usd"], 0)

    def test_q4_uncertain_call_is_not_replayed(self):
        adapter = FakeAdapter(incomplete=True)
        executor, root = self.admit(adapter, dispatch_v2())
        self.assertEqual("uncertain", executor.run(root)["state"])
        self.assertEqual("uncertain", executor.run(root)["state"])
        self.assertEqual(1, len(adapter.calls))

    def test_invalid_authority_and_policy_tamper_are_rejected(self):
        for change in ({"manifest_sha256": "bad"},
                       {"cost_ceiling_usd": 4.0},
                       {"alternative_cell": "worker-fable-max"}):
            with self.subTest(change=change):
                with tempfile.TemporaryDirectory() as temporary:
                    project = Path(temporary)
                    # Validate before actor admission or a paid invocation.
                    with self.assertRaises(ExecutorError):
                        from task_executor import _experimental_policy
                        _experimental_policy({**dispatch(), **change},
                                             FakeAdapter().capability(project), 3.0,
                                             FakeAdapter())
        adapter = FakeAdapter()
        executor, root = self.admit(adapter, dispatch())
        path = executor._path(root)
        value = _read(path)
        value["experimental_policy"]["selected_cell"] = "worker-opus-high"
        _write(path, value)
        with self.assertRaises(ExecutorError):
            executor.run(root)
        self.assertEqual([], adapter.calls)


if __name__ == "__main__":
    unittest.main()
