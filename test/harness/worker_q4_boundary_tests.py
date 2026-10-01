#!/usr/bin/env python3
"""Offline validation for Q4 policy, launcher and WSL boundary evidence."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_wsl_q4_attestation as attestation  # noqa: E402


class Q4BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(attestation.OUTPUT.read_text(encoding="utf-8"))
        frozen_sources = self.value["source_sha256"]
        patcher = patch.object(attestation, "source_hashes",
                               return_value=frozen_sources)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_saved_evidence_is_source_bound_and_provider_free(self):
        self.assertTrue(attestation.validate(self.value, check_host=False))
        self.assertEqual(0, self.value["probe"]["provider_calls"])
        self.assertEqual(0, self.value["probe"]["provider_cost_usd"])
        self.assertEqual(["worker-opus-high", "worker-sonnet-low",
                          "worker-sonnet-xhigh"],
                         self.value["probe"]["supported_cells"])
        self.assertTrue(all(self.value["probe"]["checks"].values()))

    def test_evidence_and_probe_tampering_fail_closed(self):
        for path, replacement in (("runtime_launcher_sha256", "0" * 64),
                                  ("result", "FAIL")):
            changed = copy.deepcopy(self.value)
            changed[path] = replacement
            with self.subTest(path=path):
                self.assertFalse(attestation.validate(changed, check_host=False))
        changed = copy.deepcopy(self.value)
        changed["probe"]["checks"]["writers_stopped"] = False
        self.assertFalse(attestation.validate(changed, check_host=False))

    def test_launcher_whitelist_is_exact_and_cost_bounded(self):
        script = (ROOT / "tools/worker_wsl_namespace_q4.sh").read_text(encoding="utf-8")
        self.assertIn("model_class=${BASH_REMATCH[1]}", script)
        for clause in (("sonnet", "low"), ("sonnet", "xhigh"), ("opus", "high")):
            self.assertIn(f"$model_class == {clause[0]} && $9 == {clause[1]}", script)
        self.assertIn("0 < x <= 6", script)
        self.assertIn("env -i", script)


if __name__ == "__main__":
    unittest.main()
