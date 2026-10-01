"""Reserved Q4U cases were sealed before provider outcomes and stay disjoint."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_reserve_manifest import OUTPUT, build  # noqa: E402


class Q4UReserveManifestTests(unittest.TestCase):
    def test_frozen_inventory_matches_current_seals(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen, build())
        self.assertFalse(frozen["qualification_authority"])
        self.assertEqual(["R09", "R10", "R11", "R12"],
                         [row["task_id"] for row in frozen["rows"]])
        self.assertEqual(4, len({row["mechanism"] for row in frozen["rows"]}))


if __name__ == "__main__":
    unittest.main()
