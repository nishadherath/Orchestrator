#!/usr/bin/env python3
"""R0 contracts and legacy characterisation tests for Controller-aware routing.

These tests make the pre-change boundary explicit. Legacy behaviour remains
available under a named policy for reproducible comparison.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ControllerRoutingR0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "src" / "controller_routing_contracts.json").read_text(encoding="utf-8")
        )
        cls.controller = load(ROOT / "tools" / "system_controller.py", "r0_system_controller")
        cls.worker = load(ROOT / "tools" / "evaluation_live_worker.py", "r0_live_worker")
        cls.runner = load(ROOT / "tools" / "evaluation_runner.py", "r0_evaluation_runner")

    def test_contract_freezes_modes_precedence_and_safety_boundary(self):
        value = self.contract
        self.assertEqual(value["version"], 1)
        self.assertEqual(value["current_shipped_policy_id"], "B0")
        self.assertEqual(value["controller_modes"], ["auto", "on", "off"])
        self.assertEqual(value["control_precedence_high_to_low"], [
            "explicit_operator_request_or_cli", "task", "session", "project", "shipped_default",
        ])
        self.assertFalse(value["control_contract"]["setting_change_dispatches_paid_work"])
        self.assertFalse(value["control_contract"]["untrusted_content_can_change_control"])
        self.assertFalse(value["acceptance_boundary"]["operator_constraints_mutable_by_controller"])
        self.assertFalse(value["acceptance_boundary"]["acceptance_contract_mutable_by_controller"])
        self.assertTrue(value["acceptance_boundary"]["execution_status_is_separate"])

    def test_contract_has_complete_assessment_decision_and_packet_fields(self):
        assessment = set(self.contract["rigour_assessment"]["required_fields"])
        decision = set(self.contract["routing_decision"]["required_fields"])
        packet = set(self.contract["controller_evidence_packet"]["required_fields"])
        self.assertTrue({"task_revision", "premise_uncertainty", "evidence"} <= assessment)
        self.assertTrue({"recommended_action", "effective_action", "override_revision"} <= decision)
        self.assertTrue({"acceptance_contract_digest", "verified_findings", "accounting"} <= packet)
        self.assertFalse(self.contract["rigour_assessment"]["unknown_is_false"])
        self.assertFalse(self.contract["controller_evidence_packet"]["gap_can_claim_completed_solution"])
        self.assertEqual(
            self.contract["automatic_policy"]["maximum_controller_invocations_per_task_revision"], 1
        )

    def test_r2_live_adapter_resolves_fable_explicitly(self):
        self.assertEqual(
            self.worker.cell_identity("worker-fable-low"),
            ("claude-fable-5-1", "low"),
        )

    def test_r2_evaluator_resolves_fable_explicitly(self):
        self.assertEqual(
            self.runner.expected_model("worker-fable-xhigh"),
            "claude-fable-5-1",
        )

    def test_legacy_unstable_classifier_does_not_gate_generation(self):
        scripted = self.controller._happy_path_script()
        fake = self.controller.FakeRoleRunner(
            scripted,
            classify_script={
                "controller-stability": {"stable": False, "reasoning": "material premise remains"}
            },
        )
        with tempfile.TemporaryDirectory(prefix="controller-r0-unstable-") as folder:
            result = self.controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="unstable",
                integrity_policy="legacy-quick-v0",
            )
        self.assertEqual(result.outcome, "solution")
        stability_index = fake.calls.index(("controller-stability", "controller"))
        self.assertIn(("generate", "generator"), fake.calls[stability_index + 1:])

    def test_legacy_selector_output_does_not_choose_winner(self):
        canned = self.controller._canned()
        selector_rejects_generated = [{
            "type": "SelectionRecord",
            "baseline_id": "cand-001",
            "shortlist": [],
            "excluded": [{"candidate_id": "cand-002", "reason": "loses_to_b0"}],
            "ledger_version": 2,
            "references": ["cand-001", "cand-002"],
        }]
        scripted = self.controller._happy_path_script()
        scripted[("select", "selector")] = [selector_rejects_generated]
        fake = self.controller.FakeRoleRunner(scripted)
        with tempfile.TemporaryDirectory(prefix="controller-r0-selector-") as folder:
            result = self.controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="selector",
                integrity_policy="legacy-quick-v0",
            )
        self.assertEqual(result.outcome, "solution")
        self.assertEqual(result.record["technique"], "subtract")
        self.assertEqual(canned["candidate"][0]["technique"], "subtract")


if __name__ == "__main__":
    unittest.main(verbosity=2)
