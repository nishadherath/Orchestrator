"""Frozen public-only development coverage assessments and decisions."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_assess_public import build  # noqa: E402
from worker_q4u_coverage import LOW, MEDIUM, decision  # noqa: E402


class Q4UPublicAssessmentTests(unittest.TestCase):
    def test_frozen_assessments_match_public_bytes(self):
        for task_id, expected in (("D01W", "partial"), ("D01S", "direct"),
                                  ("B02W", "partial"), ("B02S", "direct"),
                                  ("C03", "partial"), ("C04", "partial"),
                                  ("M05", "partial"), ("M06", "partial"),
                                  ("F07W", "partial"), ("F07S", "direct"),
                                  ("H08W", "partial"), ("H08S", "direct"),
                                  ("R09", "partial"), ("R10", "partial"),
                                  ("R11", "partial"), ("R12", "partial")):
            with self.subTest(task=task_id):
                frozen = json.loads((ROOT / "test/fixtures/worker_q4u_public" /
                                     task_id / "public_assessment.json").read_text(encoding="utf-8"))
                self.assertEqual(build(task_id), frozen)
                self.assertEqual(expected, frozen["assessment"]["verification_coverage"])
                expected_criteria = 1 if task_id == "M05" else 2
                self.assertEqual(expected_criteria,
                                 len(frozen["assessment"]["facts"]["criteria"]))

    def test_only_partial_coverage_proposes_a_medium_continuation(self):
        options = {"policy": "coverage_repair", "phase": "after_low",
                   "low_outcome": "no_change", "supported_cells": {LOW, MEDIUM},
                   "remaining_usd": 4.0, "call_ceiling_usd": 2.0,
                   "budget_enforced": True}
        for family in ("D01", "B02", "F07", "H08"):
            with self.subTest(family=family):
                weak = decision(build(family + "W")["assessment"], **options)
                strong = decision(build(family + "S")["assessment"], **options)
                self.assertEqual((MEDIUM, "partial_public_check_after_low_failure"),
                                 (weak["action"], weak["reason"]))
                self.assertEqual((LOW, "baseline_repair"),
                                 (strong["action"], strong["reason"]))
                self.assertFalse(weak["dispatch"] or strong["dispatch"])

    def test_investigations_stop_after_public_acceptance_without_hidden_inference(self):
        for task_id in ("C03", "C04", "M05", "M06", "R11", "R12"):
            with self.subTest(task=task_id):
                result = decision(build(task_id)["assessment"],
                                  policy="coverage_repair", phase="after_low",
                                  low_outcome="accepted",
                                  supported_cells={LOW, MEDIUM},
                                  remaining_usd=4.0, call_ceiling_usd=2.0,
                                  budget_enforced=True)
                self.assertEqual("stop", result["action"])
                self.assertEqual("accepted_without_hidden_inference", result["reason"])

    def test_cross_component_candidate_differs_only_on_coupled_tasks(self):
        for task_id, expected in (("D01W", MEDIUM), ("F07W", MEDIUM),
                                  ("R10", MEDIUM), ("B02W", LOW),
                                  ("H08W", LOW), ("R09", LOW)):
            with self.subTest(task=task_id):
                result = decision(build(task_id)["assessment"],
                                  policy="cross_component_medium", phase="initial",
                                  low_outcome=None, supported_cells={LOW, MEDIUM},
                                  remaining_usd=4.0, call_ceiling_usd=2.0,
                                  budget_enforced=True)
                self.assertEqual(expected, result["action"])
                self.assertFalse(result["dispatch"])


if __name__ == "__main__":
    unittest.main()
