#!/usr/bin/env python3
"""Offline checks for six frozen Q3 public fixtures and attack evidence."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from worker_adapter import digest  # noqa: E402
from worker_q3_public_catalogue import FIXTURES, ROOT as CATALOGUE_ROOT, build, sha  # noqa: E402

RESULTS = ROOT / "test/results"
SOURCES = (
    "tools/worker_q3_public_calibrate.py",
    "tools/worker_wsl_q3_public.py",
    "tools/worker_q3_public_catalogue.py",
    "tools/worker_wsl_q2_verify.py",
)


class Q3PublicTests(unittest.TestCase):
    def test_catalogue_and_calibration_are_bound_to_current_bytes(self) -> None:
        self.assertEqual(CATALOGUE_ROOT, ROOT)
        families = set()
        for number in range(3, 9):
            task_id = f"P{number:02d}"
            with self.subTest(task_id=task_id):
                current = build(task_id)
                frozen = json.loads((FIXTURES / task_id / "task.json").read_text(encoding="utf-8"))
                self.assertEqual(current, frozen)
                self.assertNotIn(current["source_url"], families)
                families.add(current["source_url"])
                files = list(RESULTS.glob(
                    f"*-worker-q3-{task_id.lower()}-{current['task_sha256'][:12]}-calibration.json"))
                self.assertEqual(len(files), 1)
                evidence = json.loads(files[0].read_text(encoding="utf-8"))
                self.assertEqual(evidence["result"], "PASS")
                self.assertEqual(evidence["task_sha256"], current["task_sha256"])
                self.assertEqual(evidence["evidence_sha256"], digest({
                    key: value for key, value in evidence.items()
                    if key != "evidence_sha256"}))
                self.assertEqual(evidence["source_sha256"], {
                    name: sha(ROOT / name) for name in SOURCES})
                self.assertTrue(all(evidence["checks"].values()))
                grades = evidence["grades"]
                self.assertEqual(set(grades), {"baseline", "partial", "reference", "alternative"})
                self.assertLess(grades["baseline"]["quality"], grades["partial"]["quality"])
                self.assertLess(grades["partial"]["quality"], 100)
                for variant, row in grades.items():
                    self.assertEqual(row["variant"], variant)
                    self.assertEqual(row["task_sha256"], current["task_sha256"])
                    self.assertEqual(row["grade_sha256"], digest({
                        key: value for key, value in row.items()
                        if key != "grade_sha256"}))
                    self.assertTrue(row["oracle_read_denied"])
                    self.assertEqual(row["provider_calls"], 0)
                self.assertEqual(grades["reference"]["quality"], 100)
                self.assertEqual(grades["alternative"]["quality"], 100)

    def test_adversarial_evidence_rejects_public_answer_and_protected_edits(self) -> None:
        path = RESULTS / "2026-09-25-worker-q3-public-attacks.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(row["result"], "PASS")
        self.assertEqual(row["evidence_sha256"], digest({
            key: value for key, value in row.items() if key != "evidence_sha256"}))
        self.assertEqual(row["provider_calls"], 0)
        self.assertTrue(all(row["checks"].values()))
        self.assertEqual(row["source_sha256"], {name: sha(ROOT / name)
            for name in ("tools/worker_wsl_q3_public_probe.py",
                         "tools/worker_wsl_q3_public.py",
                         "tools/worker_q3_public_catalogue.py")})


if __name__ == "__main__":
    unittest.main()
