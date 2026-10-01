"""Missing-facts controls require an objective stop and exact missing inputs."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_missing import IDS, MissingError, calibrate, check  # noqa: E402


class Q4UMissingTests(unittest.TestCase):
    def test_two_frozen_mechanisms_grade_partial_clarification(self):
        for task_id in IDS:
            with self.subTest(task=task_id):
                saved = json.loads((ROOT / "test/results" /
                                    f"2026-09-26-worker-q4u-{task_id.lower()}-calibration.json")
                                   .read_text(encoding="utf-8"))
                self.assertEqual(saved, calibrate(task_id))
                self.assertEqual([0, 40, 100],
                                 [saved["grades"][name]["score"] for name in
                                  ("baseline", "partial", "reference")])
                self.assertEqual([False, True, True],
                                 [saved["grades"][name]["public_pass"] for name in
                                  ("baseline", "partial", "reference")])

    def test_actor_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
            fixtures = Path(directory) / "fixtures"
            shutil.copytree(ROOT / "test/fixtures/worker_q4u_public/M05",
                            fixtures / "M05")
            actor = fixtures / "M05/actor/policy.py"
            actor.write_bytes(actor.read_bytes() + b"# changed\n")
            with self.assertRaises(MissingError):
                check("M05", fixtures=fixtures)

    def test_evaluator_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
            oracles = Path(directory)
            original = ROOT / "test/oracles/worker_q4u_public/M06.zip"
            (oracles / "M06.zip").write_bytes(original.read_bytes() + b"changed")
            with self.assertRaises(MissingError):
                check("M06", oracles=oracles)


if __name__ == "__main__":
    unittest.main()
