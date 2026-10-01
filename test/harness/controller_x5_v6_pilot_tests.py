#!/usr/bin/env python3
"""Provider-free invariants for the single-use X5 v6 paired pilot."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_v6_pilot as pilot  # noqa: E402


class PilotTests(unittest.TestCase):
    def test_schedule_pairs_every_task_and_caps_total_spend(self) -> None:
        rows = pilot.schedule()
        self.assertEqual(len(rows), 18)
        self.assertEqual([row["sequence"] for row in rows], list(range(1, 19)))
        self.assertEqual(sum(row["maximum_usd"] for row in rows), 144.0)
        for task in pilot.screen.TASKS:
            self.assertEqual({row["arm"] for row in rows if row["task_id"] == task},
                             {"B", "S", "A"})
        frontier = [row for row in rows
                    if row["controller_profile"] == "frontier-candidate"]
        self.assertEqual([(row["task_id"], row["arm"]) for row in frontier],
                         [("X5-MIGRATE", "A")])

    def test_notice_required_before_an_episode_can_start(self) -> None:
        manifest = {"manifest_sha256": "frozen", "episodes": pilot.schedule()}
        with self.assertRaisesRegex(pilot.PilotError, "approval"):
            pilot.gate(manifest, manifest["episodes"][0], {"approved": False})

    def test_started_marker_refuses_replay(self) -> None:
        with tempfile.TemporaryDirectory(prefix="x5-v6-marker-") as raw:
            path = Path(raw) / "001-started.json"
            pilot.exclusive(path, {"root_id": "first"})
            with self.assertRaises(FileExistsError):
                pilot.exclusive(path, {"root_id": "second"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                             {"root_id": "first"})


if __name__ == "__main__":
    unittest.main()
