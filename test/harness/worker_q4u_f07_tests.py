"""F07 weak/strong public checks share one sealed multi-file evaluator."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_f07 import F07Error, calibrate, check  # noqa: E402


class F07Tests(unittest.TestCase):
    def test_weak_and_strong_checks_share_hidden_grades(self):
        grades = []
        for task_id in ("F07W", "F07S"):
            with self.subTest(task=task_id):
                saved = json.loads((ROOT / "test/results" /
                                    f"2026-09-26-worker-q4u-{task_id.lower()}-calibration.json")
                                   .read_text(encoding="utf-8"))
                self.assertEqual(saved, calibrate(task_id))
                grades.append([saved["grades"][name]["score"] for name in
                               ("baseline", "partial", "reference")])
                expected_public = ([True, True, True] if task_id.endswith("W")
                                   else [False, False, True])
                self.assertEqual(expected_public,
                                 [saved["grades"][name]["public_pass"] for name in
                                  ("baseline", "partial", "reference")])
        self.assertEqual([[30, 65, 100], [30, 65, 100]], grades)

    def test_tampering_actor_or_evaluator_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
            path = Path(directory)
            fixtures = path / "fixtures"
            shutil.copytree(ROOT / "test/fixtures/worker_q4u_public/F07W",
                            fixtures / "F07W")
            actor = fixtures / "F07W/actor/event_ref/encode.py"
            actor.write_bytes(actor.read_bytes() + b"# changed\n")
            with self.assertRaises(F07Error):
                check("F07W", fixtures=fixtures)
            evaluator = path / "F07.zip"
            original = ROOT / "test/oracles/worker_q4u_public/F07.zip"
            evaluator.write_bytes(original.read_bytes() + b"changed")
            with self.assertRaises(F07Error):
                check("F07S", evaluator=evaluator)


if __name__ == "__main__":
    unittest.main()
