"""Provider-free checks for the prospective report transport and stop policy."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_adapter import WorkerRequest  # noqa: E402
from worker_q4t_policy import settled_stop_reason  # noqa: E402
from worker_q4t_structured import Q4TStructuredWorkerAdapter  # noqa: E402
from worker_q4r_structured import schema_argument  # noqa: E402


REPORT = {"status": "completed", "diagnosis": "Fixed the bug.",
          "evidence": ["Public check passed."], "checks": [],
          "remaining": [], "clarification": None}


class FakeAdapter(Q4TStructuredWorkerAdapter):
    def capability(self, actor_root: Path) -> dict:
        return {"configured": True}


class Q4TTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.request = WorkerRequest(
            actor_root=root, issue="Fix the public bug.",
            allowed_edits=("source.py",), requested_cell="worker-sonnet-medium",
            allowance_usd=4.0, policy="Use public evidence.",
            admission_token="admission", invocation_id="invocation",
            revision_id="revision", decision_digest="decision",
            intent_digest="intent")

    def receipt(self, *, subtype: str, structured: dict | None,
                returncode: int) -> dict:
        model = "claude-sonnet-5"
        final = {"type": "result", "subtype": subtype,
                 "total_cost_usd": 0.2, "num_turns": 14,
                 "usage": {"input_tokens": 10, "output_tokens": 20},
                 "modelUsage": {model: {"costUSD": 0.2}}}
        if structured is not None:
            final["structured_output"] = structured
        stdout = "\n".join(json.dumps(item) for item in [
            {"type": "assistant", "message": {"model": model, "content": []}},
            final]) + "\n"

        def transport(cmd, root, env, timeout):
            self.assertEqual(schema_argument(), cmd[-1])
            self.assertEqual("5", env["MAX_STRUCTURED_OUTPUT_RETRIES"])
            self.assertIn("finish immediately", cmd[2])
            return subprocess.CompletedProcess(cmd, returncode, stdout, "")

        adapter = FakeAdapter(mcp_config=self.request.actor_root / "mcp.json",
                              transport=transport)
        return adapter.run(self.request)

    def test_valid_report_retains_binding_and_bounded_diagnostics(self):
        receipt = self.receipt(subtype="success", structured=REPORT, returncode=0)
        self.assertEqual("completed", receipt["status"])
        self.assertEqual("present", receipt["evaluation_report"]["observability"])
        self.assertEqual("claude-code-json-schema-v2",
                         receipt["evaluation_transport"]["mode"])
        self.assertEqual(5, receipt["evaluation_transport"]["structured_retry_limit"])
        self.assertEqual(0, receipt["q4t_diagnostics"]["invalid_line_count"])

    def test_retry_exhaustion_fails_closed_but_settles_charge(self):
        receipt = self.receipt(subtype="error_max_structured_output_retries",
                               structured=None, returncode=1)
        self.assertEqual("failed", receipt["status"])
        self.assertTrue(receipt["terminal"])
        self.assertEqual(0.2, receipt["cost_usd"])
        self.assertEqual("transport-invalid",
                         receipt["evaluation_report"]["observability"])
        self.assertIsNone(receipt["evaluation_report"]["report"])


class Q4TPolicyTests(unittest.TestCase):
    def episode(self) -> dict:
        return {"root_state": "blocked", "protected_integrity": True,
                "qualification_eligible": False,
                "quality_v2": {"report_observability": "transport-invalid",
                               "hidden_accepted": False, "critical_error": False,
                               "inconclusive": True},
                "settlement": {"charged_usd": 0.2, "provider_calls": 1,
                               "cost_settled": True, "writer_stopped": True},
                "attempts": [{"cost_usd": 0.2, "terminal": True,
                              "writer_stopped": True, "identity_valid": True,
                              "evaluation_report": {
                                  "observability": "transport-invalid"},
                              "evaluation_transport": {
                                  "mode": "claude-code-json-schema-v2",
                                  "structured_retry_limit": 5,
                                  "structured_output_present": False},
                              "q4t_diagnostics": {
                                  "result_subtype":
                                  "error_max_structured_output_retries",
                                  "invalid_line_count": 0, "returncode": 1}}]}

    def test_settled_report_failure_can_be_scored_without_replay(self):
        self.assertIsNone(settled_stop_reason(self.episode(),
                                               episode_maximum_usd=4.0,
                                               candidate_positive=True))

    def test_other_blocked_root_and_safety_faults_stop(self):
        episode = self.episode()
        episode["attempts"][0]["q4t_diagnostics"]["result_subtype"] = "error_budget"
        self.assertIn("blocked root", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=True))
        episode = self.episode()
        episode["quality_v2"]["hidden_accepted"] = True
        self.assertIn("invalid grade", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=True))
        episode = self.episode()
        episode["protected_integrity"] = False
        self.assertIn("integrity", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=True))
        episode = self.episode()
        episode["attempts"][0]["identity_valid"] = False
        self.assertIn("identity", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=True))

    def test_critical_baseline_is_measured_but_positive_candidate_stops(self):
        episode = self.episode()
        episode["quality_v2"]["critical_error"] = True
        self.assertIsNone(settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=False))
        self.assertEqual("candidate critical error", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=True))

    def test_unproven_missing_report_stops_even_with_settled_charge(self):
        episode = self.episode()
        episode["root_state"] = "failed"
        self.assertIn("inconclusive", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=False))

    def test_charge_and_source_evidence_must_settle(self):
        episode = self.episode()
        episode["settlement"]["charged_usd"] = 0.3
        self.assertIn("charges disagree", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=True))
        episode = self.episode()
        episode["settlement"]["cost_settled"] = False
        self.assertIn("unsettled", settled_stop_reason(
            episode, episode_maximum_usd=4.0, candidate_positive=True))


if __name__ == "__main__":
    unittest.main()
