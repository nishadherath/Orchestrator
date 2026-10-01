#!/usr/bin/env python3
"""Offline checks for the installed Q4R schema boundary evidence."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_wsl_q4r_attestation as attestation  # noqa: E402


class Q4RBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(attestation.OUTPUT.read_text(encoding="utf-8"))
        frozen_sources = self.value["source_sha256"]
        patcher = patch.object(attestation, "source_hashes",
                               return_value=frozen_sources)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_provider_free_evidence_binds_schema_and_stopped_edits(self):
        self.assertTrue(attestation.validate(self.value, check_host=False))
        probe = self.value["probe"]
        self.assertEqual(0, probe["provider_calls"])
        self.assertEqual(0, probe["provider_cost_usd"])
        self.assertEqual(["worker-opus-high", "worker-sonnet-high",
                          "worker-sonnet-low"], probe["supported_cells"])
        self.assertTrue(all(probe["checks"].values()))

    def test_schema_and_runtime_tampering_fail_closed(self):
        for field in ("runtime_schema_sha256", "runtime_launcher_sha256"):
            changed = copy.deepcopy(self.value)
            changed[field] = "0" * 64
            with self.subTest(field=field):
                self.assertFalse(attestation.validate(changed, check_host=False))
        changed = copy.deepcopy(self.value)
        changed["probe"]["checks"]["schema_transport_bound"] = False
        self.assertFalse(attestation.validate(changed, check_host=False))

    def test_launcher_requires_exact_schema_and_caps_each_call(self):
        script = (ROOT / "tools/worker_wsl_namespace_q4r.sh").read_text(
            encoding="utf-8")
        self.assertIn('${21} == "--json-schema=$expected_schema"', script)
        self.assertIn('$model_class == sonnet && $9 == high', script)
        self.assertIn('0 < x <= 6', script)


if __name__ == "__main__":
    unittest.main()
