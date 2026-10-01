#!/usr/bin/env python3
"""Offline integrity checks for the Q4 public calibration evidence."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_adapter import digest  # noqa: E402
from worker_q3_public_catalogue import build  # noqa: E402
from worker_quality_v2 import parse_report, validate_rubric  # noqa: E402

EVIDENCE = ROOT / "test/results/2026-09-25-worker-q4-public-calibration.json"
SCENARIOS = {"reference", "alternative", "useful_partial", "diagnosis_only",
             "honest_incomplete", "false_completion", "wrong_diagnosis",
             "public_copy", "critical_failure"}


class Q4PublicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_evidence_and_frozen_source_bindings(self):
        value = self.value
        self.assertEqual(value["evidence_sha256"], digest({
            key: item for key, item in value.items() if key != "evidence_sha256"}))
        self.assertEqual(0, value["provider_calls"])
        self.assertEqual(0, value["provider_cost_usd"])
        self.assertEqual(["P04", "P05", "P06", "P08"], value["source_families"])
        for row in value["rows"]:
            source = build(row["task_id"])
            self.assertEqual(source["task_sha256"], row["source_task_sha256"])
            self.assertEqual(source["source_commit"], row["source_commit"])
            self.assertEqual(source["licence_sha256"], row["licence_sha256"])
            self.assertTrue(row["oracle_read_denied"])
            self.assertTrue(row["report_store_read_denied"])
            validate_rubric(row["rubric"])

    def test_scenario_matrix_distinguishes_quality_and_truthfulness(self):
        for row in self.value["rows"]:
            scenarios = {item["scenario"]: item for item in row["scenarios"]}
            self.assertEqual(SCENARIOS, set(scenarios))
            for name, item in scenarios.items():
                result = item["quality_v2"]
                self.assertEqual(result["grade_sha256"], digest({
                    key: value for key, value in result.items() if key != "grade_sha256"}))
                record = item["report_record"]
                self.assertEqual(record["raw_sha256"], hashlib.sha256(
                    record["raw_utf8"].encode("utf-8")).hexdigest())
                self.assertEqual(record["report"], parse_report(record["raw_utf8"]))
                self.assertEqual(row["q4_task_sha256"],
                                 record["binding"]["task_sha256"])
            self.assertTrue(scenarios["reference"]["quality_v2"]["hidden_accepted"])
            self.assertTrue(scenarios["alternative"]["quality_v2"]["hidden_accepted"])
            self.assertGreater(scenarios["useful_partial"]["quality_v2"]["quality"], 0)
            self.assertFalse(scenarios["honest_incomplete"]["quality_v2"][
                "unsupported_completion"])
            self.assertTrue(scenarios["false_completion"]["quality_v2"][
                "unsupported_completion"])
            self.assertEqual(0, scenarios["wrong_diagnosis"]["quality_v2"][
                "component_scores"]["diagnosis"])
            self.assertFalse(scenarios["public_copy"]["quality_v2"]["hidden_accepted"])
            self.assertTrue(scenarios["critical_failure"]["quality_v2"]["critical_error"])

    def test_only_declared_timing_sensitive_task_uses_stability_repeats(self):
        rows = {row["task_id"]: row for row in self.value["rows"]}
        for task_id in ("P04", "P06", "P08"):
            self.assertIsNone(rows[task_id]["timer_stability"])
        stability = rows["P05"]["timer_stability"]
        self.assertEqual({"baseline", "reference"}, {row["variant"] for row in stability})
        for row in stability:
            self.assertEqual(10, row["repetitions"])
            self.assertTrue(row["stable"])
            self.assertEqual(1, len(set(row["qualities"])))
            self.assertEqual(1, len(set(row["acceptance"])))


if __name__ == "__main__":
    unittest.main()
