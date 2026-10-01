#!/usr/bin/env python3
"""Offline tests for per-message live calibration adjudication."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "tools" / "live_calibration_adjudication.py"
    spec = importlib.util.spec_from_file_location("live_calibration_adjudication", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = load_module()

    def test_stream_attributes_root_worker_and_auxiliary_billing(self):
        registry = self.subject.model_registry.load()
        sonnet_id = self.subject.model_registry.resolve_cell("worker-sonnet-low", registry)["cli_model"]
        auxiliary_haiku_id = self.subject.model_registry.historical_provider_id("haiku", registry)
        rows = [
            {"type": "assistant", "parent_tool_use_id": None,
             "message": {"model": sonnet_id}},
            {"type": "assistant", "parent_tool_use_id": "toolu_worker",
             "message": {"model": sonnet_id}},
            {"type": "result", "result": "WORKER_OK", "modelUsage": {
                sonnet_id: {}, auxiliary_haiku_id: {},
            }},
        ]
        parsed = self.subject.parse_stream("\n".join(json.dumps(row) for row in rows))
        self.assertEqual(parsed["root_models"], [sonnet_id])
        self.assertEqual(parsed["worker_models"], [sonnet_id])
        self.assertEqual(parsed["auxiliary_billed_models"], [auxiliary_haiku_id])
        self.assertEqual(parsed["invalid_line_count"], 0)

    def test_invalid_stream_line_is_counted(self):
        parsed = self.subject.parse_stream("not-json\n[]\n")
        self.assertEqual(parsed["event_count"], 0)
        self.assertEqual(parsed["invalid_line_count"], 2)

    def test_validation_rejects_tampering(self):
        original_sha = self.subject.file_sha256(self.subject.ORIGINAL)
        sonnet_id = self.subject.model_registry.resolve_cell("worker-sonnet-low")["cli_model"]
        haiku_id = self.subject.model_registry.resolve_cell("worker-haiku-default")["cli_model"]
        value = {
            "schema_version": 1,
            "result": "PASS",
            "checks": {name: True for name in (
                "original_evidence_valid", "terminal_result", "one_worker_completed",
                "root_model_attributed", "worker_model_attributed",
                "billing_telemetry_present", "stream_well_formed",
            )},
            "original": {"file_sha256": original_sha},
            "attribution": {"root_models": [sonnet_id], "worker_models": [sonnet_id],
                            "billed_models": [sonnet_id, haiku_id],
                            "auxiliary_billed_models": [haiku_id]},
            "implementation_sha256": self.subject.file_sha256(
                ROOT / "tools" / "live_calibration_adjudication.py"),
        }
        value["evidence_sha256"] = self.subject.digest(value)
        with tempfile.TemporaryDirectory(prefix="adjudication-test-") as folder:
            path = Path(folder) / "evidence.json"
            self.subject.atomic_json(path, value)
            self.assertTrue(self.subject.validate(path)[0])
            value["result"] = "FAIL"
            self.subject.atomic_json(path, value)
            self.assertFalse(self.subject.validate(path)[0])

    def test_historical_receipt_validates_by_registry_class(self):
        self.assertTrue(self.subject.validate(self.subject.DEFAULT_OUTPUT)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
