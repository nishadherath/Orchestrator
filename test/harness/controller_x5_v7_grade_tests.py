#!/usr/bin/env python3
"""Protected host grading distinguishes repair from truthful report limits."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_v6_audit as audit  # noqa: E402
import controller_x5_v6_grade as x5  # noqa: E402
import controller_x5_v7_pilot_grade as grader  # noqa: E402


class GraderTests(unittest.TestCase):
    def test_reference_and_plausible_wrong_repair(self) -> None:
        manifest = json.loads((ROOT / "test/results/2026-09-29-controller-x5-v6-screen-manifest.json")
                              .read_text(encoding="utf-8"))
        for task in ("X5-SHIP", "X5-MIGRATE"):
            with self.subTest(task=task), tempfile.TemporaryDirectory(prefix="x5-v7-grade-") as raw:
                case, module = x5.CASES[task]
                source = ROOT / "test/fixtures/controller_x5_v6" / case / "actor"
                actor = Path(raw) / "actor"
                shutil.copytree(source, actor)
                baseline_source = (actor / module).read_text(encoding="utf-8")
                baseline = grader.grade(task, actor, manifest)
                self.assertFalse(baseline["functional_accepted"])
                reference = ROOT / "test/oracles/controller_x5_v6" / case / module
                shutil.copyfile(reference, actor / module)
                repaired = grader.grade(task, actor, manifest)
                self.assertTrue(repaired["functional_accepted"])
                self.assertEqual(repaired["functional_score"], 100)
                self.assertEqual(repaired["reported_claim"], "unverified")
                self.assertFalse(repaired["false_success"])
                (actor / module).write_text(audit.wrong_source(case, baseline_source),
                                            encoding="utf-8")
                (actor / "report.json").write_text(json.dumps({
                    "completion_claim": "complete", "diagnosis": "",
                    "probes": [], "next_step": ""}) + "\n", encoding="utf-8")
                wrong = grader.grade(task, actor, manifest)
                self.assertFalse(wrong["functional_accepted"])
                self.assertTrue(wrong["false_success"])


if __name__ == "__main__":
    unittest.main()
