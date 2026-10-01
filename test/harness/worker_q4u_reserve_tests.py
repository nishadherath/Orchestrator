"""Fresh R09/R10 reserve fixtures are sealed and calibrate without a provider."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_reserve import ReserveError, SPECS, calibrate, check  # noqa: E402


class Q4UReserveTests(unittest.TestCase):
    def test_disjoint_implementation_mechanisms_calibrate(self):
        for task_id in SPECS:
            with self.subTest(task=task_id):
                saved = json.loads((ROOT / "test/results" /
                                    f"2026-09-26-worker-q4u-{task_id.lower()}-calibration.json")
                                   .read_text(encoding="utf-8"))
                self.assertEqual(saved, calibrate(task_id))
                self.assertEqual([30, 65, 100],
                                 [saved["grades"][name]["score"] for name in
                                  ("baseline", "partial", "reference")])
                task = json.loads((ROOT / "test/fixtures/worker_q4u_public" /
                                   task_id / "task.json").read_text(encoding="utf-8"))
                self.assertEqual("reserved", task["split"])

    def test_actor_and_evaluator_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
            path = Path(directory)
            fixtures = path / "fixtures"
            shutil.copytree(ROOT / "test/fixtures/worker_q4u_public/R09",
                            fixtures / "R09")
            actor = fixtures / "R09/actor/frame_parser.py"
            actor.write_bytes(actor.read_bytes() + b"# changed\n")
            with self.assertRaises(ReserveError):
                check("R09", fixtures=fixtures)
            oracles = path / "oracles"
            oracles.mkdir()
            original = ROOT / "test/oracles/worker_q4u_public/R10.zip"
            (oracles / "R10.zip").write_bytes(original.read_bytes() + b"changed")
            with self.assertRaises(ReserveError):
                check("R10", oracles=oracles)


if __name__ == "__main__":
    unittest.main()
