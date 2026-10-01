"""The Q4U campaign grader matches the independently frozen calibrations."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_grade import ORACLES, IN_PROCESS, SHARED, grade  # noqa: E402


IDS = ("D01W", "D01S", "B02W", "B02S", "C03", "C04", "M05", "M06",
       "F07W", "F07S", "H08W", "H08S", "R09", "R10", "R11", "R12")


class Q4UGradeTests(unittest.TestCase):
    def test_campaign_grader_preserves_three_way_calibration(self):
        fixtures = ROOT / "test/fixtures/worker_q4u_public"
        for task_id in IDS:
            saved = json.loads((ROOT / "test/results" /
                                f"2026-09-26-worker-q4u-{task_id.lower()}-calibration.json"
                                ).read_text(encoding="utf-8"))
            prefix = task_id[:3]
            name = IN_PROCESS.get(prefix) or SHARED.get(prefix) or f"{task_id}.zip"
            with zipfile.ZipFile(ORACLES / name) as archive:
                overlays = {name: archive.read(name) for name in archive.namelist()
                            if name.startswith(("partial/", "reference/"))}
            for variant in ("baseline", "partial", "reference"):
                with self.subTest(task=task_id, variant=variant):
                    with tempfile.TemporaryDirectory(prefix="q4u-grade-") as raw:
                        actor = Path(raw) / "actor"
                        shutil.copytree(fixtures / task_id / "actor", actor)
                        expected_files = {path.relative_to(actor).as_posix()
                                          for path in actor.rglob("*") if path.is_file()}
                        for relative, data in overlays.items():
                            if relative.startswith(variant + "/"):
                                (actor / relative.split("/", 1)[1]).write_bytes(data)
                        result = grade(task_id, actor)
                        self.assertEqual(saved["grades"][variant]["score"], result["score"])
                        self.assertEqual(expected_files, {
                            path.relative_to(actor).as_posix()
                            for path in actor.rglob("*") if path.is_file()})
                        self.assertEqual(0, result["provider_calls"])


if __name__ == "__main__":
    unittest.main()
