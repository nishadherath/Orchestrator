#!/usr/bin/env python3
"""Provider-free validation of the complete no-replay Q4 M3 result."""
from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import model_registry  # noqa: E402
import worker_q4_screen as original  # noqa: E402
import worker_q4_screen_continue as continuation  # noqa: E402
import worker_q4_screen_live as live  # noqa: E402
from worker_adapter import digest  # noqa: E402


class Q4ResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(original.MANIFEST.read_text(encoding="utf-8"))
        cls.manifest = json.loads(continuation.MANIFEST.read_text(encoding="utf-8"))
        cls.campaign = json.loads((continuation.RUN / "campaign.json").read_text(
            encoding="utf-8"))
        cls.decision = json.loads((continuation.RUN / "decision.json").read_text(
            encoding="utf-8"))

    def test_campaign_is_complete_settled_and_no_replay(self):
        campaign = self.campaign
        self.assertEqual(digest({key: value for key, value in campaign.items()
                                 if key != "state_sha256"}),
                         campaign["state_sha256"])
        self.assertEqual("complete", campaign["status"])
        self.assertEqual(list(range(1, 17)),
                         [row["sequence"] for row in campaign["rows"]])
        self.assertEqual(["inherited-graded"] * 3,
                         [row["state"] for row in campaign["rows"][:3]])
        self.assertTrue(all(row["state"] == "graded"
                            for row in campaign["rows"][3:]))
        attempts = [attempt for row in campaign["rows"]
                    for attempt in row["episode"]["attempts"]]
        self.assertEqual(16, len(attempts))
        self.assertTrue(all(attempt["terminal"] and attempt["writer_stopped"]
                            for attempt in attempts))
        self.assertAlmostEqual(sum(row["episode"]["budget"]["spent_usd"]
                                   for row in campaign["rows"]),
                               campaign["total_cost_usd"], places=8)
        self.assertEqual(sum(len(row["episode"]["attempts"])
                             for row in campaign["rows"]),
                         campaign["total_provider_calls"])
        self.assertEqual(9.849044605, campaign["total_cost_usd"])
        self.assertEqual(16, campaign["total_provider_calls"])
        self.assertLessEqual(campaign["total_cost_usd"], 99)
        self.assertLessEqual(campaign["total_provider_calls"], 51)

    def test_every_episode_remains_bound_to_cell_report_and_snapshot(self):
        rows = {row["sequence"]: row for row in self.original["rows"]}
        terminal_failures = []
        for item in self.campaign["rows"]:
            expected = rows[item["sequence"]]
            episode = item["episode"]
            self.assertEqual((expected["task_id"], expected["episode_label"]),
                             (episode["task_id"], episode["episode_label"]))
            self.assertEqual(digest({key: value for key, value in
                                     episode["quality_v2"].items()
                                     if key != "grade_sha256"}),
                             episode["quality_v2"]["grade_sha256"])
            self.assertEqual(digest({key: value for key, value in
                                     episode["snapshot"].items()
                                     if key != "snapshot_sha256"}),
                             episode["snapshot"]["snapshot_sha256"])
            self.assertEqual({name: value for name, value in
                              expected["actor_files"].items()
                              if name not in expected["editable_paths"]},
                             episode["protected_sha256"])
            for index, attempt in enumerate(episode["attempts"]):
                cell = expected["ladder"][index]
                self.assertEqual(cell, attempt["requested_cell"])
                self.assertEqual(model_registry.resolve_cell(cell)["cli_model"],
                                 attempt["actual_model"])
                report = attempt["evaluation_report"]
                self.assertEqual(digest(report),
                                 attempt["evaluation_report_digest"])
                self.assertEqual(cell, report["binding"]["requested_cell"])
                self.assertEqual(expected["task_sha256"],
                                 report["binding"]["task_sha256"])
            if episode.get("terminal_failure"):
                terminal_failures.append(item["sequence"])
        self.assertEqual([3, 16], terminal_failures)

    def test_decision_reproduces_and_retains_b0(self):
        decision = self.decision
        self.assertEqual(digest({key: value for key, value in decision.items()
                                 if key != "state_sha256"}),
                         decision["state_sha256"])
        body = {key: value for key, value in decision.items()
                if key not in {"decision_sha256", "state_sha256"}}
        self.assertEqual(digest(body), decision["decision_sha256"])
        state = {"rows": [{"state": "graded", "episode": row["episode"]}
                          for row in self.campaign["rows"]]}
        reproduced = live.analyse(state, self.manifest)
        self.assertEqual(reproduced,
                         {key: value for key, value in decision.items()
                          if key != "state_sha256"})
        self.assertEqual("retain-b0", decision["policy_decision"])
        self.assertIsNone(decision["selected_candidate"])
        self.assertEqual(2, decision["reserved_repetitions_if_q4_freezes"])
        self.assertFalse(any(row["qualifies"] for row in decision["candidates"]))
        self.assertTrue(math.isclose(
            sum(row["cost_usd"] for row in decision["summaries"].values()),
            self.campaign["total_cost_usd"], abs_tol=1e-8))


if __name__ == "__main__":
    unittest.main()
