"""Provider-free checks for the non-replayed Q4T corpus and screen freeze."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_adapter import digest  # noqa: E402
from worker_q4t_public import FAMILIES, UPSTREAM, build, rubric, triggers  # noqa: E402
from worker_q4t_public_grade import build_evidence  # noqa: E402
from worker_q4t_screen import MANIFEST, build_manifest, live_rubric, screen_rows  # noqa: E402


class Q4TScreenTests(unittest.TestCase):
    def test_t07_calibration_separates_baseline_partial_reference(self):
        value = build_evidence()
        self.assertEqual([0, 40, 100], [row["executable_score"] for row in value["grades"]])
        self.assertFalse(value["grades"][0]["public_pass"])
        self.assertTrue(value["grades"][2]["public_pass"])
        self.assertEqual(digest(rubric("T07")), value["grades"][0]["quality_rubric_sha256"])

    def test_five_upstream_tasks_are_not_in_prior_paid_s4_family(self):
        self.assertEqual(6, len(FAMILIES))
        self.assertEqual({"S01", "S02", "S04", "S05", "S06"}, set(UPSTREAM))
        self.assertEqual(4, sum(row["triggered"] for row in triggers().values()))
        self.assertEqual("authored-synthetic-cross-module-atomicity-regression",
                         build("T07")["origin"])

    def test_balanced_arm_inventory_and_live_rubrics(self):
        rows = screen_rows()
        self.assertEqual(18, len(rows))
        for task_id in FAMILIES:
            arms = [row for row in rows if row["task_id"] == task_id]
            self.assertEqual({"b0-a", "b0-b", "sonnet-medium"},
                             {row["episode_label"] for row in arms})
            self.assertEqual(1, len({row["source_task_sha256"] for row in arms}))
            self.assertEqual(1, len({digest(live_rubric(row)) for row in arms}))

    def test_manifest_is_reproducible_and_binds_policy(self):
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(value, build_manifest(value["date_utc"]))
        self.assertEqual("score-with-zero-report-credit",
                         value["stop_policy"]["settled_report_failure"])
        self.assertEqual("claude-code-json-schema-v2", value["transport_mode"])
        self.assertEqual(5, value["structured_retry_limit"])
        self.assertEqual(54, value["cost"]["maximum_provider_calls"])
        self.assertEqual(72.0, value["cost"]["maximum_allocation_usd"])


if __name__ == "__main__":
    unittest.main()
