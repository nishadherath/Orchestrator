#!/usr/bin/env python3
"""Offline attack cases for Q1 path and attestation validation."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_wsl_q1 as boundary  # noqa: E402
import worker_wsl_q1_attestation as attestation  # noqa: E402


class Q1BoundaryTests(unittest.TestCase):
    def test_manifest_paths_cannot_escape_or_claim_private_work_areas(self) -> None:
        for value in ("", "/tmp/out.py", "../oracle.py", "src/../../oracle.py",
                      "src\\oracle.py", "src//main.py", "src/./main.py",
                      "src/..", ".scratch/answer.py", "graft/answer.py",
                      ".gitignore", "src/a b.py"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                boundary.path_parts(value)
        self.assertEqual(("src", "main.py"), boundary.path_parts("src/main.py"))

    def test_attestation_rejects_rewritten_outcomes_even_with_valid_digest(self) -> None:
        value = {"result": "PASS", "source_sha256": {}, "runtime_sha256": {},
                 "n4_host_evidence_sha256": "host",
                 "probe": {"result": "PASS", "checks": {key: True for key in attestation.EXPECTED},
                           "check_count": len(attestation.EXPECTED),
                           "provider_calls": 0, "provider_cost_usd": 0},
                 "accounting_checks": {key: True for key in attestation.ACCOUNTING_EXPECTED}}
        value["evidence_sha256"] = attestation.digest(value)
        with (mock.patch.object(attestation, "sources", return_value={}),
              mock.patch.object(attestation, "host_digest", return_value="host")):
            self.assertTrue(attestation.validate(value, check_host=False))
            for edit in (lambda row: row["probe"]["checks"].pop("evaluator_direct_denied"),
                         lambda row: row["probe"].__setitem__("provider_cost_usd", 0.1),
                         lambda row: row["accounting_checks"].pop("unknown_charge_retains_hold")):
                attacked = copy.deepcopy(value)
                edit(attacked)
                attacked["evidence_sha256"] = attestation.digest(
                    {key: item for key, item in attacked.items() if key != "evidence_sha256"})
                self.assertFalse(attestation.validate(attacked, check_host=False))


if __name__ == "__main__":
    unittest.main()
