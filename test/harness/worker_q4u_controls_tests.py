"""Synthetic no-edit controls separate correct investigation from needless edits."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_controls import ControlError, IDS, calibrate, check  # noqa: E402


class Q4UControlsTests(unittest.TestCase):
    def test_two_distinct_frozen_controls_grade_no_edit_correct(self):
        for task_id in IDS:
            with self.subTest(task=task_id):
                saved = json.loads((ROOT / "test/results" /
                                    f"2026-09-26-worker-q4u-{task_id.lower()}-calibration.json")
                                   .read_text(encoding="utf-8"))
                self.assertEqual(saved, calibrate(task_id))
                self.assertEqual([100, 0, 100],
                                 [saved["grades"][name]["score"] for name in
                                  ("baseline", "partial", "reference")])
                task = json.loads((ROOT / "test/fixtures/worker_q4u_public" /
                                   task_id / "task.json").read_text(encoding="utf-8"))
                self.assertEqual("investigation", task["task_kind"])
                self.assertFalse(task["change_required"])

    def test_actor_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
            fixtures = Path(directory) / "fixtures"
            shutil.copytree(ROOT / "test/fixtures/worker_q4u_public/C03",
                            fixtures / "C03")
            actor = fixtures / "C03/actor/allocation.py"
            actor.write_bytes(actor.read_bytes() + b"# changed\n")
            with self.assertRaises(ControlError):
                check("C03", fixtures=fixtures)

    def test_evaluator_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
            oracles = Path(directory)
            original = ROOT / "test/oracles/worker_q4u_public/C04.zip"
            altered = oracles / "C04.zip"
            altered.write_bytes(original.read_bytes() + b"changed")
            with self.assertRaises(ControlError):
                check("C04", oracles=oracles)


if __name__ == "__main__":
    unittest.main()
