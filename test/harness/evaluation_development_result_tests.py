#!/usr/bin/env python3
"""Regression tests for the recorded W07 development result."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    name = "evaluation_development_result"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / "evaluation_development_result.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DevelopmentResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = load_module()

    def test_recorded_evidence_validates(self):
        valid, detail = self.subject.validate()
        self.assertTrue(valid, detail)

    def test_aggregate_reconciles_policy_and_decision(self):
        value = self.subject.aggregate()
        policies = {row["policy_id"]: row for row in value["policy_summary"]}
        self.assertEqual(value["result"], "PASS", value)
        self.assertEqual(value["budget"]["known_spend_usd"], 1.376153606)
        self.assertEqual(policies["B0"]["accepted"], 11)
        self.assertEqual(policies["B1"]["accepted"], 12)
        self.assertEqual(value["decision"]["baseline_retained"], "B0")
        self.assertEqual(value["decision"]["adaptive_candidate"], "B1")
        self.assertTrue(value["decision"]["proceed_to_w08"])
        self.assertFalse(value["decision"]["default_changed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
