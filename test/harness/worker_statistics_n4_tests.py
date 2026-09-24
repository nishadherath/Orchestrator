#!/usr/bin/env python3
"""N4's frozen task-level paired gate and conservative sample preflight."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import worker_statistics as stats  # noqa: E402


class StatisticsTests(unittest.TestCase):
    def test_cp_endpoints_and_joint_bound(self):
        self.assertEqual(0, stats.cp_lower(0, 12))
        self.assertEqual(1, stats.cp_upper(12, 12))
        self.assertAlmostEqual(1 - .0125 ** (1 / 12), stats.cp_upper(0, 12))
        self.assertAlmostEqual(.0125 ** (1 / 12), stats.cp_lower(12, 12))
        rows = [{"b0_accept": True, "candidate_accept": True,
                 "b0_quality": 70, "candidate_quality": 70} for _ in range(12)]
        result = stats.bounds(rows)
        self.assertEqual(0, result["acceptance_delta"])
        self.assertLess(result["acceptance_lower"], -.05)
        self.assertLess(result["quality_lower"], -5)
        self.assertEqual(12, result["tasks"])

    def test_invalid_data_and_extreme_gain(self):
        with self.assertRaises(ValueError):
            stats.bounds([])
        with self.assertRaises(ValueError):
            stats.bounds([{"b0_accept": 1, "candidate_accept": True,
                           "b0_quality": 0, "candidate_quality": math.nan}])
        rows = [{"b0_accept": False, "candidate_accept": True,
                 "b0_quality": 0, "candidate_quality": 100} for _ in range(12)]
        result = stats.bounds(rows)
        self.assertGreater(result["acceptance_lower"], -.05)
        self.assertGreater(result["quality_lower"], 5)

    def test_preflight_is_reproducible_and_moderate_effect_is_inconclusive(self):
        result = stats.simulate(trials=100)
        self.assertEqual(result, stats.simulate(trials=100))
        self.assertGreater(result["quality_penalty_points"], 70)
        self.assertEqual(0, result["scenarios"]["modest_gain"]["fraction_passing_both_quality_floors"])


if __name__ == "__main__":
    unittest.main()
