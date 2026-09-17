#!/usr/bin/env python3
"""Offline regression tests for the paid pilot launch boundary."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    name = "evaluation_pilot"
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "evaluation_pilot.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = load_module()

    def test_offline_qualification(self):
        with tempfile.TemporaryDirectory(prefix="pilot-tests-") as folder:
            value = self.subject.run_qualification(Path(folder))
        self.assertEqual(value["result"], "PASS", value)
        self.assertEqual(value["model_calls"], 0)

    def test_authorisation_template_is_deliberately_inactive(self):
        template = json.loads(self.subject.AUTHORISATION_TEMPLATE.read_text(encoding="utf-8"))
        candidate = {
            "candidate_sha256": "a" * 64, "source_revision": "offline",
            "source_dirty": False, "bundle": {"version": "offline"},
            "isolation": {"evidence_sha256": "b" * 64}, "blockers": [],
        }
        manifest = self.subject.pilot_manifest(lambda: candidate)
        with tempfile.TemporaryDirectory(prefix="pilot-auth-") as folder:
            path = Path(folder) / "authorisation.json"
            path.write_text(json.dumps(template), encoding="utf-8")
            valid, _, _ = self.subject.validate_authorisation(path, manifest)
        self.assertFalse(valid)

    def test_recorded_evidence_rejects_tampering(self):
        source = json.loads(self.subject.DEFAULT_EVIDENCE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="pilot-evidence-",
                                         dir=ROOT / "test" / "results") as folder:
            path = Path(folder) / "evidence.json"
            self.subject.evaluation_runner.atomic_json(path, source)
            self.assertTrue(self.subject.validate_evidence(path)[0])
            source["model_calls"] = 1
            self.subject.evaluation_runner.atomic_json(path, source)
            self.assertFalse(self.subject.validate_evidence(path)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
