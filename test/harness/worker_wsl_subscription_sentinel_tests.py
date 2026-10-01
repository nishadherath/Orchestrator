#!/usr/bin/env python3
"""Provider-free parsing checks for the subscription Read-denial sentinel."""
from __future__ import annotations

import json
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import model_registry  # noqa: E402
import worker_wsl_attestation as host  # noqa: E402
from worker_wsl_subscription_sentinel import (  # noqa: E402
    TARGET, REQUIRED_CHECKS, _blocks, validate)
import worker_wsl_subscription_sentinel as sentinel  # noqa: E402


def stream(result_text: str, *, tool_input: object = None) -> str:
    call = {"type": "assistant", "message": {"content": [{
        "type": "tool_use", "name": "Read", "id": "tool-1",
        "input": {"file_path": TARGET} if tool_input is None else tool_input}]}}
    result = {"type": "user", "message": {"content": [{
        "type": "tool_result", "tool_use_id": "tool-1",
        "is_error": True, "content": result_text}]}}
    terminal = {"type": "result", "subtype": "success", "total_cost_usd": 0.01}
    return "\n".join(json.dumps(x) for x in (call, result, terminal))


class SentinelParserTests(unittest.TestCase):
    def test_permission_denial_is_distinct_from_missing_file(self) -> None:
        verdicts, terminal = _blocks(stream("Read denied: outside working directory"))
        self.assertEqual("success", terminal["subtype"])
        self.assertEqual(1, len(verdicts))
        self.assertTrue(verdicts[0]["denied"])
        self.assertFalse(verdicts[0]["missing_file_only"])

    def test_missing_file_is_not_a_denial(self) -> None:
        verdicts, _ = _blocks(stream("No such file"))
        self.assertEqual(1, len(verdicts))
        self.assertFalse(verdicts[0]["denied"])
        self.assertTrue(verdicts[0]["missing_file_only"])

    def test_malformed_tool_input_is_ignored(self) -> None:
        verdicts, _ = _blocks(stream("Permission denied", tool_input="invalid"))
        self.assertEqual([], verdicts)

    def test_sealed_passing_evidence_and_tampering(self) -> None:
        body = {"schema_version": 1, "result": "PASS",
                "checks": {key: True for key in REQUIRED_CHECKS},
                "source_sha256": host.sha(Path(sentinel.__file__)),
                "requested_cell": "worker-sonnet-low", "requested_effort": "low",
                "served_effort": None, "read_attempts": 1, "returncode": 0,
                "terminal_subtype": "success", "failure_category": None,
                "served_model": model_registry.resolve_cell("worker-sonnet-low")
                ["expected_provider_model"],
                "reported_api_equivalent_cost_usd": 0.01}
        evidence = {**body, "evidence_sha256": hashlib.sha256(
            host.canonical(body)).hexdigest()}
        self.assertTrue(validate(evidence))
        evidence["checks"]["read_denied"] = False
        self.assertFalse(validate(evidence))


if __name__ == "__main__":
    unittest.main()
