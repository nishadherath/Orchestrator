#!/usr/bin/env python3
"""Offline tests for live calibration evidence parsing and validation."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "live_calibration", ROOT / "tools" / "live_calibration.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LiveCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calibration = load_module()

    def test_rollup_detects_descendant_usage(self):
        raw = {
            "total_cost_usd": 0.04,
            "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 20,
                "cache_read_input_tokens": 30, "output_tokens": 40,
                "iterations": [{
                    "input_tokens": 2, "cache_creation_input_tokens": 3,
                    "cache_read_input_tokens": 4, "output_tokens": 5,
                }],
            },
            "modelUsage": {"claude-sonnet-5": {"costUSD": 0.04}},
        }
        evidence = self.calibration.rollup_evidence(raw)
        self.assertTrue(evidence["descendant_usage_present"])
        self.assertTrue(evidence["model_cost_matches_total"])
        self.assertEqual(self.calibration.actual_models(raw), ["claude-sonnet-5"])

    def test_unknown_usage_stays_unknown(self):
        self.assertEqual(
            self.calibration.usage_record({"input_tokens": -1, "output_tokens": "4"}),
            {field: None for field in self.calibration.USAGE_FIELDS},
        )

    def test_evidence_validation_rejects_tampering(self):
        checks = {name: True for name in (
            "direct_terminal", "spawn_terminal", "actual_model", "disjoint_usage",
            "parent_child_rollup", "timeout_retained", "wsl_mediated_boundary")}
        value = {"result": "PASS", "checks": checks,
                 "implementation_sha256": self.calibration.file_sha256(
                     ROOT / "tools" / "live_calibration.py")}
        value["evidence_sha256"] = self.calibration.digest(value)
        with tempfile.TemporaryDirectory(prefix="calibration-evidence-") as folder:
            path = Path(folder) / "evidence.json"
            self.calibration.atomic_json(path, value)
            self.assertTrue(self.calibration.validate(path)[0])
            changed = json.loads(path.read_text(encoding="utf-8"))
            changed["checks"]["actual_model"] = False
            self.calibration.atomic_json(path, changed)
            self.assertFalse(self.calibration.validate(path)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
