#!/usr/bin/env python3
"""Offline guard for the frozen H03 development actor and private oracle."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "test" / "fixtures" / "controller_x5_h03"


class H03FixtureTests(unittest.TestCase):
    def test_frozen_catalogue_and_isolation(self):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools" / "controller_x5_h03_freeze.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        catalogue = json.loads((FIXTURE / "catalogue.json").read_text(encoding="utf-8"))
        self.assertEqual(catalogue["editable_paths"], ["tools/system_controller.py"])
        self.assertEqual(catalogue["risk"]["controls"][0]["decision"], "do-not-review")
        self.assertEqual(catalogue["risk"]["controls"][1]["decision"], "clarify")
        self.assertFalse((FIXTURE / "actor" / "oracle.py").exists())
        self.assertFalse((FIXTURE / "actor" / "variants").exists())

    def test_baseline_partial_and_two_complete_repairs(self):
        with tempfile.TemporaryDirectory(prefix="controller-x5-h03-gate-") as folder:
            output = Path(folder) / "probe.json"
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "test" / "results" /
                                           "2026-09-30-controller-x5-h03-probe.py"),
                 "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            probe = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(
            [probe[name]["oracle"]["score"] for name in
             ("baseline", "partial", "alternative", "reference")],
            [10, 45, 100, 100],
        )
        self.assertTrue(probe["partial"]["oracle"]["critical_error"])
        self.assertFalse(probe["alternative"]["oracle"]["critical_error"])
        self.assertFalse(probe["reference"]["oracle"]["critical_error"])

    def test_public_only_risk_gate_is_frozen_separately(self):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools" / "controller_x5_h03_risk.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        risk = json.loads((FIXTURE / "risk-manifest.json").read_text(encoding="utf-8"))
        catalogue = json.loads((FIXTURE / "catalogue.json").read_text(encoding="utf-8"))
        self.assertEqual(risk["source_catalogue_sha256"], catalogue["catalogue_sha256"])
        self.assertTrue(risk["stop_if_public_risk_passes"])
        self.assertFalse((FIXTURE / "actor" / "risk_check.py").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
