#!/usr/bin/env python3
"""Provider-free Q4S transport, settlement and no-replay regression cases."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_adapter import WorkerRequest, digest  # noqa: E402
from worker_q4s_admission import (Q4SAdmissionError, mark_intent,  # noqa: E402
                                  settle_episode, settle_stopped_patch,
                                  start_campaign)
from worker_q4s_structured import Q4SStructuredWorkerAdapter  # noqa: E402


class FakeAdapter(Q4SStructuredWorkerAdapter):
    def capability(self, actor_root: Path) -> dict:
        return {"configured": True}


def report() -> dict:
    return {"status": "partial", "diagnosis": "A public check still fails.",
            "evidence": ["public check failure"],
            "checks": [{"command": "python3 -B public_check.py",
                        "outcome": "failed"}],
            "remaining": ["repair source"], "clarification": None}


def stream(*, model: str = "claude-sonnet-5", structured: bool = True,
           subtype: str = "success", errors: list | None = None,
           malformed: bool = False) -> str:
    final = {"type": "result", "subtype": subtype,
             "total_cost_usd": 0.25, "num_turns": 3,
             "result": "PRIVATE MODEL RESULT",
             "usage": {"input_tokens": 4, "output_tokens": 8},
             "modelUsage": {model: {"costUSD": 0.25}}}
    if structured:
        final["structured_output"] = report()
    if errors is not None:
        final["errors"] = errors
    events = [
        {"type": "assistant", "message": {"model": "<synthetic>", "content": []}},
        {"type": "assistant", "message": {"model": model, "content": []}},
        final,
    ]
    output = "\n".join(json.dumps(item) for item in events) + "\n"
    return output + ("not-json\n" if malformed else "")


def preflight() -> dict:
    value = {"result": "PASS", "source_sha256": {"adapter": "a" * 64},
             "auth": {"result": "PASS", "provider_calls": 0,
                      "provider_cost_usd": 0},
             "probe": {"result": "PASS", "provider_calls": 0,
                       "provider_cost_usd": 0}}
    return {**value, "evidence_sha256": digest(value)}


class Q4SS1Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "protected.txt").write_text("protected\n", encoding="utf-8")
        self.request = WorkerRequest(
            actor_root=self.root, issue="Fix source.py", allowed_edits=("source.py",),
            requested_cell="worker-sonnet-medium", allowance_usd=4.0,
            policy="Use public checks.", admission_token="admission",
            invocation_id="invocation", revision_id="revision",
            decision_digest="decision", intent_digest="intent")

    def receipt(self, output: str, *, returncode: int = 0,
                stderr: str = "PRIVATE STDERR") -> dict:
        def transport(command, root, env, timeout):
            self.assertEqual("20", env["CLAUDE_CODE_MAX_TURNS"])
            self.assertEqual("2", env["MAX_STRUCTURED_OUTPUT_RETRIES"])
            self.assertEqual("8192", env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"])
            self.assertEqual("--json-schema", command[-1].split("=", 1)[0])
            return subprocess.CompletedProcess(command, returncode, output, stderr)
        return FakeAdapter(mcp_config=self.root / "fake-mcp.json",
                           transport=transport).run(self.request)

    def stopped_outcome(self, receipt: dict) -> dict:
        return {"state": "blocked", "attempts": [{
            "invocation_id": receipt["invocation_id"], "receipt": receipt}],
            "budget": {"unresolved": False, "spent_usd": receipt["cost_usd"],
                       "invocations": {receipt["invocation_id"]: {
                           "state": "settled", "cost_usd": receipt["cost_usd"]}}}}

    def grade_and_preserve(self, receipt: dict) -> dict:
        def grade(workspace, root_state, evidence):
            self.assertEqual("blocked", root_state)
            self.assertEqual("transport-invalid", evidence["observability"])
            return ({"cases_passed": 2, "cases_total": 8},
                    {"quality": 15, "report_observability": "transport-invalid"})
        def preserve(workspace):
            return {"source.py": hashlib.sha256(
                (workspace / "source.py").read_bytes()).hexdigest()}
        protected = {"protected.txt": hashlib.sha256(
            (self.root / "protected.txt").read_bytes()).hexdigest()}
        return settle_stopped_patch(self.stopped_outcome(receipt), self.root,
                                    protected, grade, preserve)

    def test_success_without_structured_output_is_charged_and_partially_graded(self):
        receipt = self.receipt(stream(structured=False))
        self.assertEqual("failed", receipt["status"])
        self.assertTrue(receipt["terminal"])
        self.assertTrue(receipt["identity_valid"])
        self.assertEqual(["<synthetic>"], receipt["q4s_diagnostics"][
            "synthetic_root_markers"])
        self.assertEqual(["claude-sonnet-5"], receipt["q4s_diagnostics"][
            "real_root_models"])
        self.assertFalse(receipt["q4s_diagnostics"][
            "structured_output_field_present"])
        self.assertEqual(3, receipt["q4s_diagnostics"]["num_turns"])
        self.assertNotIn("PRIVATE MODEL RESULT", json.dumps(receipt))
        self.assertNotIn("PRIVATE STDERR", json.dumps(receipt))
        episode = self.grade_and_preserve(receipt)
        self.assertEqual(2, episode["executable_grade"]["cases_passed"])
        self.assertEqual(0.25, episode["settlement"]["charged_usd"])
        self.assertFalse(episode["qualification_eligible"])
        campaign = self.root / "campaign"
        start_campaign(campaign, "b" * 64, preflight)
        mark_intent(campaign, 1, "P08", "medium")
        state = settle_episode(campaign, {**episode, "task_id": "P08",
                                           "episode_label": "medium"})
        self.assertEqual("blocked", state["status"])
        self.assertEqual(0.25, state["total_cost_usd"])
        self.assertEqual("terminal-failed", state["rows"][0]["state"])
        with self.assertRaises(Q4SAdmissionError):
            mark_intent(campaign, 1, "P08", "medium")

    def test_retry_limit_and_nonzero_exit_are_settled_failures(self):
        receipt = self.receipt(stream(
            structured=False, subtype="error_max_structured_output_retries",
            errors=[{"code": "MAX_STRUCTURED_OUTPUT_RETRIES",
                     "message": "PRIVATE ERROR DETAIL"}]), returncode=1)
        self.assertEqual("failed", receipt["status"])
        self.assertEqual("transport-invalid",
                         receipt["evaluation_report"]["observability"])
        self.assertEqual(["MAX_STRUCTURED_OUTPUT_RETRIES"],
                         receipt["q4s_diagnostics"]["error_codes"])
        self.assertEqual(1, receipt["q4s_diagnostics"]["returncode"])
        self.assertNotIn("PRIVATE ERROR DETAIL", json.dumps(receipt))
        self.assertEqual(0.25, self.grade_and_preserve(receipt)[
            "settlement"]["charged_usd"])

    def test_substitution_and_malformed_stream_cannot_qualify(self):
        substitute = self.receipt(stream(model="claude-opus-5"))
        self.assertFalse(substitute["identity_valid"])
        self.assertEqual("failed", substitute["status"])
        child = json.dumps({"type": "assistant", "parent_tool_use_id": "child",
                            "message": {"model": "claude-haiku-4-5",
                                        "content": []}}) + "\n"
        delegated = self.receipt(child + stream())
        self.assertFalse(delegated["identity_valid"])
        self.assertEqual("failed", delegated["status"])
        malformed = self.receipt(stream(malformed=True))
        self.assertEqual(1, malformed["stream"]["invalid_line_count"])
        self.assertEqual("failed", malformed["status"])

    def test_valid_report_does_not_hide_nonzero_process_exit(self):
        receipt = self.receipt(stream(), returncode=1)
        self.assertEqual("present", receipt["evaluation_report"]["observability"])
        self.assertEqual("failed", receipt["status"])
        self.assertTrue(receipt["terminal"])

    def test_raw_byte_hashes_and_duplicate_results_are_bounded(self):
        raw_stdout = stream().encode("utf-8") + b"\xff"
        raw_stderr = b"private stderr\xff"
        def transport(command, root, env, timeout):
            return subprocess.CompletedProcess(command, 0, raw_stdout, raw_stderr)
        receipt = FakeAdapter(
            mcp_config=self.root / "fake-mcp.json", transport=transport).run(
                self.request)
        self.assertEqual(hashlib.sha256(raw_stdout).hexdigest(),
                         receipt["q4s_diagnostics"]["stdout_sha256"])
        self.assertEqual(hashlib.sha256(raw_stderr).hexdigest(),
                         receipt["q4s_diagnostics"]["stderr_sha256"])
        self.assertEqual("failed", receipt["status"])
        duplicate = self.receipt(stream() + stream())
        self.assertEqual(2, duplicate["q4s_diagnostics"]["event_types"]["result"])
        self.assertEqual("failed", duplicate["status"])

    def test_auth_failure_does_not_create_campaign_or_intent(self):
        campaign = self.root / "campaign"
        def expired():
            value = {**preflight(), "auth": {
                "result": "FAIL", "provider_calls": 0, "provider_cost_usd": 0}}
            return {**value, "evidence_sha256": digest({
                key: item for key, item in value.items()
                if key != "evidence_sha256"})}
        with self.assertRaises(Q4SAdmissionError):
            start_campaign(campaign, "b" * 64, expired)
        self.assertFalse(campaign.exists())
        forged = {**preflight(), "evidence_sha256": "c" * 64}
        with self.assertRaises(Q4SAdmissionError):
            start_campaign(campaign, "b" * 64, lambda: forged)
        self.assertFalse(campaign.exists())
        invalid_source = {**preflight(), "source_sha256": {"adapter": "source"}}
        invalid_source["evidence_sha256"] = digest({
            key: item for key, item in invalid_source.items()
            if key != "evidence_sha256"})
        with self.assertRaises(Q4SAdmissionError):
            start_campaign(campaign, "b" * 64, lambda: invalid_source)
        self.assertFalse(campaign.exists())

    def test_protected_drift_blocks_grade_and_snapshot(self):
        receipt = self.receipt(stream(structured=False))
        (self.root / "protected.txt").write_text("drift\n", encoding="utf-8")
        called = []
        with self.assertRaises(Q4SAdmissionError):
            settle_stopped_patch(
                self.stopped_outcome(receipt), self.root,
                {"protected.txt": hashlib.sha256(b"protected\n").hexdigest()},
                lambda *_: called.append("grade"), lambda *_: called.append("save"))
        self.assertEqual([], called)


if __name__ == "__main__":
    unittest.main()
