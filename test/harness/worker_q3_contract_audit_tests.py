#!/usr/bin/env python3
"""Regression checks for the retrospective Q3 contract sensitivity audit."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_q3_contract_audit as audit  # noqa: E402
from worker_adapter import digest  # noqa: E402


class ContractAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(audit.OUTPUT.read_text(encoding="utf-8"))
        cls.rows = {row["task_id"]: row for row in cls.evidence["rows"]}

    def test_evidence_preserves_frozen_grades_and_binds_probes(self):
        value = self.evidence
        self.assertEqual(value["audit_sha256"], digest({
            key: item for key, item in value.items() if key != "audit_sha256"}))
        self.assertEqual(value["provider_calls"], 0)
        self.assertFalse(value["frozen_grades_modified"])
        for task, expected in (("P03", 55), ("P07", 90)):
            row = self.rows[task]
            self.assertEqual(row["frozen_quality"], expected)
            self.assertFalse(row["frozen_hidden_acceptance"])
            self.assertTrue(row["source_workspace_unchanged"])
            self.assertEqual(row["probe_sha256"], digest(audit.PROBES[task]))
            self.assertEqual(row["assessment"], audit.assess(task, row["observed"]))

    def test_punctuation_is_not_a_semantic_failure(self):
        observed = copy.deepcopy(self.rows["P03"]["observed"])
        self.assertTrue(audit.assess("P03", observed)["contract_sensitivity_supported"])
        for key in ("multiple_commands", "multiple_options"):
            observed[key]["output"] = observed[key]["output"].replace(
                "one of ", "one of: ")
        self.assertTrue(audit.assess("P03", observed)["contract_sensitivity_supported"])

    def test_wrong_order_missing_name_success_exit_and_bad_control_fail(self):
        for key, field, value in (
            ("multiple_commands", "output", "Did you mean one of 'refine', 'declare'?"),
            ("multiple_options", "output", "Did you mean '--bound'?"),
            ("multiple_commands", "exit_code", 0),
            ("valid_options", "exit_code", 1),
            ("unrelated", "output", "Did you mean 'deploy'?"),
        ):
            observed = copy.deepcopy(self.rows["P03"]["observed"])
            observed[key][field] = value
            with self.subTest(key=key, field=field):
                self.assertFalse(audit.assess("P03", observed)["contract_sensitivity_supported"])

    def test_malformed_state_must_actually_be_rejected(self):
        observed = copy.deepcopy(self.rows["P07"]["observed"])
        self.assertTrue(audit.assess("P07", observed)["contract_sensitivity_supported"])
        observed["invalid_marker"]["rejected"] = False
        self.assertFalse(audit.assess("P07", observed)["contract_sensitivity_supported"])


if __name__ == "__main__":
    unittest.main()
