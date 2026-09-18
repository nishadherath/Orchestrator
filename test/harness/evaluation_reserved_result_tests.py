#!/usr/bin/env python3
"""Regression tests for the recorded W08 reserved result."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    name = "evaluation_reserved_result"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / "evaluation_reserved_result.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ReservedResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = load_module()

    def test_recorded_evidence_validates(self):
        valid, detail = self.subject.validate()
        self.assertTrue(valid, detail)

    def test_release_gate_rejects_b1_and_selects_b0(self):
        value = self.subject.aggregate()
        policies = {row["policy_id"]: row for row in value["policy_summary"]}
        self.assertEqual(value["result"], "PASS", value)
        self.assertEqual(value["budget"]["known_spend_usd"], 1.053580005)
        self.assertEqual(policies["B0"]["accepted"], 12)
        self.assertEqual(policies["B1"]["accepted"], 10)
        self.assertFalse(value["promotion_gates"]["promotion_gate_passed"])
        self.assertEqual(value["decision"]["qualified_default"], "B0")
        self.assertEqual(value["decision"]["candidate_not_promoted"], "B1")
        self.assertEqual(value["decision"]["package_policy"], "B0")
        self.assertTrue(value["decision"]["proceed_to_w09"])
        self.assertEqual(
            value["decision"]["paired_acceptance_wins"],
            {"B0": 2, "B1": 0, "ties": 22},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
