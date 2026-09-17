#!/usr/bin/env python3
"""Offline Stage 6 operational diagnostic regressions."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import preflight  # noqa: E402


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="diagnostics-test-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / ".claude").mkdir()
        (self.project / "src").mkdir()
        (self.project / "src" / "routing_priors.json").write_text(
            json.dumps({"generated_on": "2026-09-16"}), encoding="utf-8")

    def write_ledger(self, *entries: dict) -> None:
        path = self.project / ".claude" / "routing-ledger.jsonl"
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8")

    @staticmethod
    def attempt(ident: str, requested: str, actual: str | None, effort: str | None,
                outcome: str, status: str, cost: float | None) -> dict:
        return {"id": ident, "requested_cell": requested, "actual_model": actual,
                "effort_evidence": effort, "outcome": outcome, "execution_status": status,
                "usage": {"cost_usd": cost}}

    def test_actual_requested_unresolved_acceptance_and_cost(self):
        self.write_ledger({
            "id": "led-001", "first_cell": "worker-sonnet-low", "final_outcome": "unknown",
            "attempts": [
                self.attempt("att-001", "worker-sonnet-low", "claude-opus", "tasks row: high",
                             "fail", "failed", 0.25),
                self.attempt("att-002", "worker-opus-high", None, None, "unknown", "running", None),
            ],
            "acceptance": {"status": "review_required"},
        })
        value = preflight.operational_diagnostics(self.project, detailed=True)
        self.assertEqual(value["routing"]["model_or_effort_mismatches"], 1)
        self.assertEqual(value["routing"]["unresolved_attempts"], 1)
        self.assertEqual(value["routing"]["unobserved_actuals"], 1)
        self.assertEqual(value["acceptance"]["counts"], {"review_required": 1})
        self.assertEqual(value["costs"]["routing_ledger"]["known_spent_usd"], 0.25)
        self.assertEqual(value["costs"]["routing_ledger"]["unknown_attempts"], 1)

    def test_controller_budget_and_graft_configuration(self):
        run = self.project / "runs" / "run-1"
        run.mkdir(parents=True)
        (run / "budget-status.json").write_text(json.dumps({
            "spent_usd": 1.25, "reserved_usd": 0.75, "unresolved": ["call-2"], "breached": False,
        }), encoding="utf-8")
        (self.project / ".mcp.json").write_text(json.dumps({
            "mcpServers": {"graft": {"command": "graft"}},
        }), encoding="utf-8")
        (self.project / "graft").mkdir()
        value = preflight.operational_diagnostics(self.project, detailed=True)
        controller = value["costs"]["controller_runs"]
        self.assertEqual(controller["known_spent_usd"], 1.25)
        self.assertEqual(controller["reserved_usd"], 0.75)
        self.assertEqual(controller["unknown_invocations"], 1)
        self.assertTrue(value["graft"]["configured_for_claude"])
        self.assertTrue(value["graft"]["local_graph_present"])

    def test_invalid_inputs_are_reported_without_mutation(self):
        ledger = self.project / ".claude" / "routing-ledger.jsonl"
        ledger.write_text("{broken\n", encoding="utf-8")
        priors = self.project / "src" / "routing_priors.json"
        priors.write_text("{}", encoding="utf-8")
        before = ledger.read_bytes(), priors.read_bytes()
        value = preflight.operational_diagnostics(self.project)
        self.assertEqual(len(value["routing"]["ledger_errors"]), 1)
        self.assertIsNotNone(value["priors"]["error"])
        self.assertEqual(before, (ledger.read_bytes(), priors.read_bytes()))

    def test_empty_project_has_stable_shape(self):
        value = preflight.operational_diagnostics(self.project)
        self.assertEqual(set(value), {"routing", "acceptance", "costs", "priors", "graft"})
        self.assertEqual(value["routing"]["ledger_entries"], 0)
        self.assertEqual(value["acceptance"]["counts"], {})


if __name__ == "__main__":
    unittest.main()
