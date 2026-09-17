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

    def test_profiles_are_disjoint_complete_and_separately_authorised(self):
        candidate = {
            "candidate_sha256": "a" * 64, "source_revision": "offline",
            "source_dirty": False, "bundle": {"version": "offline"},
            "isolation": {"evidence_sha256": "b" * 64}, "blockers": [],
        }
        checkpoint = self.subject.pilot_manifest(
            lambda: candidate, self.subject.CHECKPOINT_PROFILE)
        continuation = self.subject.pilot_manifest(
            lambda: candidate, self.subject.CONTINUATION_PROFILE)
        checkpoint_ids = {row["episode_id"] for row in checkpoint["episodes"]}
        continuation_ids = {row["episode_id"] for row in continuation["episodes"]}
        self.assertEqual(len(checkpoint_ids), 6)
        self.assertEqual(len(continuation_ids), 18)
        self.assertTrue(checkpoint_ids.isdisjoint(continuation_ids))
        self.assertEqual([row["sequence"] for row in continuation["episodes"]],
                         list(range(7, 25)))
        self.assertEqual(continuation["cost"]["combined_authorisation_ceiling_usd"], 74.0)
        authorisation = {
            "schema_version": 1, "decision": "approved",
            "candidate_sha256": checkpoint["candidate_sha256"],
            "manifest_sha256": checkpoint["manifest_sha256"],
            "maximum_authorised_usd": 26.0,
            "approved_at": "test-clock", "approved_by": "test",
        }
        with tempfile.TemporaryDirectory(prefix="pilot-profile-auth-") as folder:
            path = Path(folder) / "authorisation.json"
            path.write_text(json.dumps(authorisation), encoding="utf-8")
            self.assertTrue(self.subject.validate_authorisation(path, checkpoint)[0])
            self.assertFalse(self.subject.validate_authorisation(path, continuation)[0])

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
