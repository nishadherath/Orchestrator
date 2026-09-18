#!/usr/bin/env python3
"""Regression tests for the reserved-qualified B0 shipping policy."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


def load_route():
    spec = importlib.util.spec_from_file_location("qualified_default_route", ROOT / "tools" / "route.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["qualified_default_route"] = module
    spec.loader.exec_module(module)
    return module


class QualifiedDefaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.route = load_route()
        cls.priors = json.loads((ROOT / "src" / "routing_priors.json").read_text(encoding="utf-8"))

    def test_every_assessment_uses_exact_b0_sequence(self):
        hostile_ledger = [{
            "bucket": "open/long/consequential",
            "first_cell": "worker-sonnet-low",
            "escalations": [{"cell": "worker-opus-high", "outcome": "fail"}],
            "final_outcome": "fail",
        }] * 20
        for sensitivity in ("mechanical", "structured", "open"):
            for horizon in ("short", "medium", "long"):
                for blast in ("contained", "consequential"):
                    for prior_failure in ("none", "failed_at_xhigh"):
                        with self.subTest(sensitivity=sensitivity, horizon=horizon,
                                          blast=blast, prior_failure=prior_failure):
                            result = self.route.plan(
                                sensitivity, horizon, blast,
                                prior_failure=prior_failure,
                                priors=self.priors, ledger=hostile_ledger,
                            )
                            self.assertEqual(result["policy"], "B0")
                            self.assertEqual(result["first"], "worker-sonnet-low")
                            self.assertEqual(
                                result["execution_ladder"],
                                ["worker-sonnet-low", "worker-sonnet-low",
                                 "worker-opus-high"],
                            )
                            self.assertIsNone(result["controller"])

    def test_cli_reports_b0_and_never_controller(self):
        line = ("assessment: open, long, consequential; self_directed: true; "
                "prior_failure: failed_at_xhigh")
        with tempfile.TemporaryDirectory(prefix="qualified-default-") as folder:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "route.py"),
                 "--from-line", line, "--project", folder, "--explain"],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("qualified default B0 sequence", completed.stdout)
        self.assertIn("Controller disabled", completed.stdout)
        self.assertEqual(completed.stdout.strip().splitlines()[-1], "worker-sonnet-low")


if __name__ == "__main__":
    unittest.main(verbosity=2)
