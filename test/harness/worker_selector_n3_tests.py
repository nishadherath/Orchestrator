#!/usr/bin/env python3
"""Provider-free N3 selector, journal and command identity checks."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import model_registry  # noqa: E402
import worker_selector  # noqa: E402
from task_executor import TaskExecutor, ExecutorError  # noqa: E402
from worker_adapter import WorkerAdapter, WorkerRequest  # noqa: E402


def facts(**changes):
    value = {"task_kind": "implementation", "complexity": "routine",
             "verification": "executable", "context_tokens": 2500,
             "deadline_seconds": None, "failure_cause": "none",
             "prior_local_repairs": 0, "frame_confidence": "clear",
             "required_artefacts": ["output.txt"],
             "evidence": [{"source": "operator", "reference": "task", "claim": "produce output"}]}
    value.update(changes)
    return value


def override(cell, **changes):
    value = {"cell": cell, "actor": "operator", "authority_id": "override_1",
             "reason": "experimental cell inspection", "max_cost_usd": 2.0}
    value.update(changes)
    return value


class SelectorTests(unittest.TestCase):
    def setUp(self):
        self.cells = set(model_registry.load()["cells"])

    def choose(self, value=None, **options):
        return worker_selector.select(worker_selector.assess(value or facts()),
                                      supported_cells=self.cells, remaining_usd=3,
                                      budget_enforced=True, **options)

    def test_every_cell_is_resolved_and_explicitly_selectable(self):
        for name in sorted(self.cells):
            with self.subTest(cell=name):
                decision = self.choose(override=override(name))
                self.assertEqual(15, len(decision["cells"]))
                self.assertEqual(name, decision["selected_cell"])
                self.assertEqual(1, sum(row["eligible"] for row in decision["cells"]))
                self.assertEqual("unqualified", next(row for row in decision["cells"]
                                                      if row["cell"] == name)["qualification"]["live_quality"])

    def test_public_facts_not_wording_or_hidden_labels(self):
        first = worker_selector.assess(facts())
        second = worker_selector.assess(facts(evidence=[{"source": "operator",
                                                      "reference": "reworded task",
                                                      "claim": "write result"}]))
        self.assertEqual(first["evidence_cohort"], second["evidence_cohort"])
        self.assertEqual(self.choose()["selected_cell"],
                         worker_selector.select(second, supported_cells=self.cells,
                                                remaining_usd=3, budget_enforced=True)["selected_cell"])
        for change in ({"hidden_grade": "pass"}, {"corpus_family": "F1"},
                       {"reserved_task_id": "R1"}):
            with self.assertRaises(worker_selector.AssessmentError):
                worker_selector.assess({**facts(), **change})
        with self.assertRaises(worker_selector.AssessmentError):
            worker_selector.assess(facts(evidence=[]))
        with self.assertRaises(worker_selector.AssessmentError):
            worker_selector.assess(facts(evidence=[{"source": "hidden_grader",
                                                       "reference": "x", "claim": "pass"}]))

    def test_failure_taxonomy_and_uncertain_frame(self):
        expected = {"missing_facts": "clarification", "context_overflow": "decompose",
                    "infrastructure": "blocked_host", "permission": "blocked_host",
                    "identity": "blocked_host", "accounting": "blocked_host"}
        for cause, stop in expected.items():
            self.assertEqual(stop, self.choose(facts(failure_cause=cause))["stop"])
        self.assertEqual("unresolved_frame", self.choose(facts(frame_confidence="uncertain"))["stop"])
        self.assertEqual("repair_exhausted", self.choose(facts(failure_cause="local_failure",
                                                               prior_local_repairs=1))["stop"])
        self.assertEqual("worker-sonnet-low", self.choose(facts(failure_cause="local_failure"))["selected_cell"])

    def test_budget_host_uncertainty_and_invalid_override(self):
        decision = self.choose(override=override("worker-fable-max", max_cost_usd=None))
        self.assertEqual("override_rejected", decision["stop"])
        self.assertIn("unknown_cost_requires_ceiling", next(row for row in decision["cells"]
                      if row["cell"] == "worker-fable-max")["reasons"])
        decision = self.choose(facts(deadline_seconds=1000),
                               override=override("worker-fable-max"))
        self.assertEqual("override_rejected", decision["stop"])
        self.assertIn("wall_unknown_with_deadline", next(row for row in decision["cells"]
                      if row["cell"] == "worker-fable-max")["reasons"])
        decision = worker_selector.select(worker_selector.assess(facts()),
                                         supported_cells={"worker-sonnet-low"},
                                         remaining_usd=0.01, budget_enforced=True)
        self.assertIsNone(decision["selected_cell"])
        self.assertEqual("no_qualified_candidate", decision["stop"])
        with self.assertRaises(worker_selector.AssessmentError):
            self.choose(override=override("worker-haiku-low"))
        self.assertEqual("override_rejected",
                         self.choose(override=override("worker-sonnet-low", max_cost_usd=4))["stop"])
        with self.assertRaises(worker_selector.AssessmentError):
            self.choose(facts(deadline_seconds=float("nan")))
        self.assertEqual("unknown_not_discounted", self.choose()["cache_reuse"])
        self.assertIn("worker-sonnet-medium", self.choose()["eligible_alternatives"])
        self.assertEqual("historical_task_mean_not_current_quote",
                         next(row for row in self.choose()["cells"]
                              if row["cell"] == "worker-sonnet-low")["cost_uncertainty"])

    def test_fake_command_pins_each_model_and_effort(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "mcp.json"
            config.write_text(json.dumps({"mcpServers": {"graft": {
                "command": sys.executable, "args": ["graft", "mcp", "${CLAUDE_PROJECT_DIR:-.}"]}}}))
            adapter = WorkerAdapter(config)
            for name in self.cells:
                row = model_registry.resolve_cell(name)
                request = WorkerRequest(root, "Produce output", ("output.txt",), name,
                                        1.0, worker_selector.POLICY, admission_token="a",
                                        invocation_id="i", revision_id="r",
                                        decision_digest="d", intent_digest="t")
                command = adapter.command(request)
                self.assertEqual(row["cli_model"], command[command.index("--model") + 1])
                self.assertEqual(row["effort"], command[command.index("--effort") + 1])
                self.assertNotIn("--model-fallback", command)


class JournalTests(unittest.TestCase):
    def test_shadow_record_does_not_relabel_b0(self):
        from test.harness.worker_executor_n1_tests import FakeAdapter
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "protected.txt").write_text("fixed")
            contract = root / "acceptance.json"
            contract.write_text(json.dumps({"version": 1, "kind": "command",
                "criteria": ["accepted output"], "constraints": [],
                "required_outputs": ["output.txt"], "protected_paths": ["protected.txt"],
                "command": [sys.executable, "-c", "from pathlib import Path; import sys; sys.exit(0 if Path('output.txt').read_text() == 'accepted' else 1)"],
                "timeout_s": 10}))
            class Host(FakeAdapter):
                def capability(self, project):
                    return {**super().capability(project), "supported_cells": sorted(model_registry.load()["cells"]),
                            "budget_enforced": True}
            adapter = Host()
            executor = TaskExecutor(root, adapter)
            executor.admit(goal="Produce output", scope=["output.txt"],
                           permissions=["read", "edit"], acceptance_path=contract,
                           budget_usd=3, authority_id="grant", actor="operator", root_id="root")
            proposal = executor.shadow_select("root", worker_selector.assess(facts()),
                                              override=override("worker-fable-high"))
            self.assertEqual("worker-fable-high", proposal["decision"]["selected_cell"])
            self.assertEqual("worker-sonnet-low", proposal["b0_cell"])
            self.assertEqual(1, proposal["sequence"])
            with self.assertRaises(ExecutorError):
                executor.shadow_select("root", worker_selector.assess(facts()),
                                       override=override("worker-opus-high"))
            result = executor.run("root")
            self.assertEqual("accepted", result["state"])
            self.assertEqual("B0", result["admission"]["policy"])
            self.assertEqual("worker-sonnet-low", adapter.calls[0].requested_cell)
            self.assertEqual("worker-sonnet-low", result["attempts"][0]["requested_cell"])
            self.assertEqual(proposal["decision_digest"], result["shadow_decisions"][0]["decision_digest"])

    def test_override_during_host_call_is_future_only(self):
        from test.harness.worker_executor_n1_tests import FakeAdapter
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "protected.txt").write_text("fixed")
            contract = root / "acceptance.json"
            contract.write_text(json.dumps({"version": 1, "kind": "command",
                "criteria": ["accepted output"], "constraints": [],
                "required_outputs": ["output.txt"], "protected_paths": ["protected.txt"],
                "command": [sys.executable, "-c", "from pathlib import Path; import sys; sys.exit(0 if Path('output.txt').read_text() == 'accepted' else 1)"],
                "timeout_s": 10}))
            class Host(FakeAdapter):
                def capability(self, project):
                    return {**super().capability(project), "supported_cells": sorted(model_registry.load()["cells"]),
                            "budget_enforced": True}

                def run(self, request):
                    if not self.calls:
                        self.proposal = self.executor.shadow_select(
                            "root", worker_selector.assess(facts()),
                            override=override("worker-opus-high"))
                    return super().run(request)
            adapter = Host(fail_count=1)
            executor = TaskExecutor(root, adapter)
            adapter.executor = executor
            executor.admit(goal="Produce output", scope=["output.txt"],
                           permissions=["read", "edit"], acceptance_path=contract,
                           budget_usd=3, authority_id="grant", actor="operator", root_id="root")
            result = executor.run("root")
            self.assertEqual("accepted", result["state"])
            self.assertEqual(2, adapter.proposal["sequence"])
            self.assertEqual(["worker-sonnet-low", "worker-sonnet-low"],
                             [call.requested_cell for call in adapter.calls])
            self.assertIsNone(adapter.proposal["decision"]["selected_cell"])
            self.assertEqual("override_rejected", adapter.proposal["decision"]["stop"])


if __name__ == "__main__":
    unittest.main()
