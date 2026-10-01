#!/usr/bin/env python3
"""Provider-free regression checks for prospective structured reports."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import model_registry  # noqa: E402
from worker_adapter import WorkerRequest  # noqa: E402
from worker_q4r_structured import (StructuredEvaluationWorkerAdapter,
                                   report_schema, schema_argument)  # noqa: E402


class FakeAdapter(StructuredEvaluationWorkerAdapter):
    def capability(self, actor_root: Path) -> dict:
        return {"configured": True}


def report() -> dict:
    return {"status": "partial", "diagnosis": "Public check still fails.",
            "evidence": ["public check failure"],
            "checks": [{"command": "python3 -B public_check.py",
                        "outcome": "failed"}],
            "remaining": ["repair cache identity"], "clarification": None}


class Q4RStructuredTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.request = WorkerRequest(
            actor_root=self.root, issue="Fix the public bug.",
            allowed_edits=("source.py",), requested_cell="worker-sonnet-low",
            allowance_usd=1.0, policy="Use public evidence.",
            admission_token="admission", invocation_id="invocation",
            revision_id="revision", decision_digest="decision",
            intent_digest="intent")

    def run_with(self, final: dict) -> dict:
        model = model_registry.resolve_cell("worker-sonnet-low")["cli_model"]
        events = [
            {"type": "assistant", "message": {"model": model, "content": []}},
            {"type": "result", "subtype": "success", "total_cost_usd": 0.1,
             "usage": {"input_tokens": 10, "output_tokens": 20},
             "modelUsage": {model: {"costUSD": 0.1}}, **final},
        ]
        stdout = "\n".join(json.dumps(event) for event in events) + "\n"
        def transport(cmd, root, env, timeout):
            self.assertEqual(schema_argument(), cmd[-1])
            return subprocess.CompletedProcess(cmd, 0, stdout, "")
        return FakeAdapter(mcp_config=self.root / "fake-mcp.json",
                           transport=transport).run(self.request)

    def test_schema_matches_local_field_contract_and_argv(self):
        schema = report_schema()
        self.assertEqual(set(schema["properties"]), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["checks"]["items"]["additionalProperties"])
        self.assertEqual(schema, json.loads(schema_argument().split("=", 1)[1]))

    def test_structured_object_wins_over_prose_without_rewriting_history(self):
        receipt = self.run_with({"result": "Here is my report in Markdown.",
                                 "structured_output": report()})
        self.assertEqual("present", receipt["evaluation_report"]["observability"])
        self.assertEqual(report(), receipt["evaluation_report"]["report"])
        self.assertEqual("claude-code-json-schema-v1",
                         receipt["evaluation_transport"]["mode"])
        self.assertTrue(receipt["evaluation_transport"]["canonicalised"])
        self.assertEqual("completed", receipt["status"])

    def test_missing_structured_output_is_transport_invalid(self):
        receipt = self.run_with({"result": json.dumps(report())})
        self.assertEqual("transport-invalid",
                         receipt["evaluation_report"]["observability"])
        self.assertFalse(receipt["evaluation_transport"]["canonicalised"])
        self.assertIsNone(receipt["evaluation_report"]["report"])

    def test_local_bounds_still_reject_oversized_schema_valid_object(self):
        oversized = {**report(), "diagnosis": "x" * 17000}
        receipt = self.run_with({"result": "", "structured_output": oversized})
        self.assertEqual("worker-malformed",
                         receipt["evaluation_report"]["observability"])
        self.assertIsNone(receipt["evaluation_report"]["report"])

    def test_non_json_structured_object_fails_closed_with_settled_cost(self):
        receipt = self.run_with({"structured_output": {**report(), "extra": float("nan")}})
        self.assertEqual("transport-invalid",
                         receipt["evaluation_report"]["observability"])
        self.assertEqual(0.1, receipt["cost_usd"])


if __name__ == "__main__":
    unittest.main()
