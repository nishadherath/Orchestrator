"""Offline gates for the prospective, non-promoting Q4U paid canary."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_adapter import digest  # noqa: E402
from worker_q4u_canary_manifest import build, rows  # noqa: E402
from worker_q4u_canary_live import CanaryError, _adjudicate, analyse  # noqa: E402


class Q4UCanaryTests(unittest.TestCase):
    def test_schedule_uses_distinct_mechanisms_and_predeclared_ladders(self):
        selected = rows()
        self.assertEqual(10, len(selected))
        self.assertEqual(4, len({row["mechanism"] for row in selected}))
        self.assertEqual(30, sum(len(row["ladder"]) for row in selected))
        self.assertEqual(40, sum(row["episode_maximum_usd"] for row in selected))
        for sequence, row in enumerate(selected, 1):
            self.assertEqual(sequence, row["sequence"])
            self.assertTrue(row["task_sha256"])
            if row["arm"] == "cross_component_medium":
                self.assertEqual("worker-sonnet-medium", row["ladder"][0])

    def test_incomplete_and_false_success_are_measured_without_promotion(self):
        manifest = build("2026-09-26", "0" * 64)
        baseline, treatment = manifest["rows"][:2]

        def episode(row, score, *, false_success=False):
            attempt = {"requested_cell": row["ladder"][0],
                       "identity_valid": True, "terminal": True,
                       "writer_stopped": True, "boundary": {"source": "attested"},
                       "cost_usd": 0.1, "wall_clock_s": 1,
                       "evaluation_report": {"observability": "present"}}
            value = {"manifest_sha256": manifest["manifest_sha256"],
                     "sequence": row["sequence"], "task_id": row["task_id"],
                     "episode_label": row["arm"], "protected_integrity": True,
                     "settlement": {"charged_usd": 0.1, "cost_settled": True},
                     "attempts": [attempt],
                     "quality_v2": {"quality": score,
                                    "false_success": false_success}}
            return {**value, "evidence_sha256": digest(value)}

        incomplete = episode(baseline, 40)
        unsafe = episode(treatment, 80, false_success=True)
        self.assertIsNone(_adjudicate(baseline, incomplete, manifest))
        self.assertIsNone(_adjudicate(treatment, unsafe, manifest))
        state = {"status": "complete", "rows": [
            {"state": "graded", "episode": incomplete},
            {"state": "graded", "episode": unsafe}],
            "total_provider_calls": 2, "total_cost_usd": 0.2}
        outcome = analyse(state, manifest)
        self.assertFalse(outcome["qualification_authority"])
        self.assertEqual("incomplete", outcome["status"])
        self.assertEqual("retain-b0-incomplete", outcome["policy_decision"])
        self.assertEqual(40, incomplete["quality_v2"]["quality"])
        altered = {**incomplete, "protected_integrity": False}
        with self.assertRaises(CanaryError):
            _adjudicate(baseline, altered, manifest)


if __name__ == "__main__":
    unittest.main()
