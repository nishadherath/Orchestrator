"""Provider-free C1 checks for the source-bound Q4T canary and settlement."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_q4s_admission as journal  # noqa: E402
import worker_q4t_canary_live as canary  # noqa: E402
from worker_adapter import digest  # noqa: E402
import model_registry  # noqa: E402
from worker_quality_v2 import report_evidence  # noqa: E402


REPORT = {"status": "completed", "diagnosis": "Repaired the canary parser.",
          "evidence": ["The public check passed."], "checks": [],
          "remaining": [], "clarification": None}


class Q4TCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = json.loads(canary.screen.MANIFEST.read_text(encoding="utf-8"))
        launcher_sha = canary.screen.sha(
            ROOT / "tools/worker_wsl_namespace_q4t.sh")
        with patch.object(canary, "frozen_parent", return_value=cls.parent), \
                patch.object(canary.screen, "runtime_sha", return_value=launcher_sha):
            cls.stage = canary.build_manifest("2026-09-26")

    def episode(self, *, report_present: bool = True) -> dict:
        cell = canary.CELLS[0]
        actor = self.parent["canary"]
        after = {actor["editable_paths"][0]: "a" * 64}
        binding = {name: "b" * 64 for name in (
            "invocation_id", "revision_id", "stream_sha256",
            "task_sha256", "prompt_sha256")}
        issue = (ROOT / "test/fixtures/worker_q4s_canary/actor/ISSUE.md").read_text(
            encoding="utf-8")
        intent = digest({"stage": self.stage["manifest_sha256"], "sequence": 1})
        binding.update(
            final_revision_sha256=digest(after), requested_cell=cell,
            invocation_id=intent[:32],
            revision_id=digest({"intent": intent, "kind": "revision"})[:32],
            task_sha256=digest({"issue": issue,
                                "allowed_edits": tuple(actor["editable_paths"])}))
        report = report_evidence(json.dumps(REPORT) if report_present else None,
                                 binding, transport_valid=report_present)
        diagnostics = {"invalid_line_count": 0,
                       "result_subtype": ("success" if report_present else
                                          "error_max_structured_output_retries")}
        current_model = model_registry.resolve_cell(cell)["cli_model"]
        item = {
            "task_id": "Q4T-CANARY", "episode_label": cell,
            "parent_manifest_sha256": self.parent["manifest_sha256"],
            "stage_manifest_sha256": self.stage["manifest_sha256"],
            "settlement": {"charged_usd": 0.2, "provider_calls": 1,
                           "writer_stopped": True, "cost_settled": True},
            "qualification_eligible": report_present,
            "receipt": {"requested_cell": cell, "actual_model": current_model,
                        "root_models": [current_model],
                        "status": "completed" if report_present else "failed",
                        "terminal": True, "writer_stopped": True,
                        "identity_valid": True,
                        "report_observability": report["observability"],
                        "report_digest": digest(report), "report": report,
                        "diagnostics": diagnostics,
                        "boundary": {"changed_paths": [actor["editable_paths"][0]],
                                     "q1_record_sha256": "c" * 64,
                                     "q1_spec_sha256": "d" * 64,
                                     "after_sha256": after},
                        "transport": {"mode": "claude-code-json-schema-v2",
                                      "structured_retry_limit": 5,
                                      "schema_sha256": self.stage["report_schema_sha256"],
                                      "structured_output_present": report_present}},
            "protected_sha256": {name: value for name, value in
                                 actor["actor_files"].items()
                                 if name not in actor["editable_paths"]},
            "snapshot": {"files": {}},
            "executable_grade": {"isolated": True, "public_pass": False},
            "quality_v2": {"scored": False},
        }
        return {**item, "evidence_sha256": digest(item)}

    def test_manifest_binds_one_call_and_new_runtime(self):
        self.assertEqual(1, self.stage["maximum_provider_calls"])
        self.assertEqual(3, self.stage["maximum_allocation_usd"])
        self.assertEqual(5, self.stage["structured_retry_limit"])
        self.assertIn("tools/worker_q4t_canary_live.py", self.stage["source_sha256"])

    def test_approval_rejects_a_changed_manifest_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "approval.json"
            path.write_text(json.dumps({
                "schema_version": 1, "decision": "approved",
                "manifest_sha256": "0" * 64,
                "maximum_authorised_usd": 3.0,
                "maximum_provider_calls": 1,
                "credential_method": "claude-code-wsl-subscription",
                "approved_at_utc": "2026-09-26T00:00:00+00:00"}),
                encoding="utf-8")
            with patch.object(canary, "APPROVAL", path), \
                    self.assertRaises(canary.CanaryError):
                canary.validate_approval(self.stage)

    def test_success_and_settled_missing_report(self):
        good = self.episode()
        canary.validate_episode(good, canary.CELLS[0], self.parent, self.stage)
        failure = self.episode(report_present=False)
        canary.validate_episode(failure, canary.CELLS[0], self.parent, self.stage)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "campaign"
            proof = {"result": "PASS", "source_sha256": {"driver": "a" * 64},
                     "auth": {"result": "PASS", "provider_calls": 0,
                              "provider_cost_usd": 0},
                     "probe": {"result": "PASS", "provider_calls": 0,
                               "provider_cost_usd": 0}}
            proof["evidence_sha256"] = digest(proof)
            journal.start_campaign(path, self.stage["manifest_sha256"],
                                   lambda: proof)
            journal.mark_intent(path, 1, "Q4T-CANARY", canary.CELLS[0])
            state = journal.settle_episode(path, failure)
            self.assertEqual("blocked", state["status"])
            self.assertEqual(1, state["total_provider_calls"])
            self.assertEqual(0.2, state["total_cost_usd"])

    def test_forged_report_and_identity_are_rejected(self):
        altered = self.episode()
        altered["receipt"]["report"]["raw_utf8"] = "{}"
        altered["receipt"]["report_digest"] = digest(altered["receipt"]["report"])
        altered["evidence_sha256"] = digest({
            key: value for key, value in altered.items() if key != "evidence_sha256"})
        with self.assertRaises(canary.CanaryError):
            canary.validate_episode(altered, canary.CELLS[0], self.parent,
                                    self.stage)
        wrong = self.episode()
        wrong["receipt"]["actual_model"] = model_registry.resolve_cell(
            "worker-opus-high")["cli_model"]
        wrong["evidence_sha256"] = digest({
            key: value for key, value in wrong.items() if key != "evidence_sha256"})
        with self.assertRaises(canary.CanaryError):
            canary.validate_episode(wrong, canary.CELLS[0], self.parent,
                                    self.stage)

    def test_driver_settles_terminal_report_failure_once(self):
        failure = self.episode(report_present=False)
        proof = {"schema_version": 1, "result": "PASS",
                 "source_sha256": {"driver": "a" * 64},
                 "auth": {"result": "PASS", "provider_calls": 0,
                          "provider_cost_usd": 0},
                 "probe": {"result": "PASS", "provider_calls": 0,
                           "provider_cost_usd": 0}}
        proof["evidence_sha256"] = digest(proof)
        response = subprocess.CompletedProcess(
            [], 0, json.dumps({"result": "COMPLETE", "episode": failure}), "")

        frozen_date = dt.date.fromisoformat(self.stage["date_utc"])

        class FrozenClock:
            @staticmethod
            def now(timezone):
                return dt.datetime.combine(frozen_date, dt.time.min,
                                           tzinfo=timezone)

        historical_clock = types.SimpleNamespace(date=dt.date, datetime=FrozenClock,
                                                 timezone=dt.timezone)
        with tempfile.TemporaryDirectory() as raw, \
                patch.object(canary, "RUN", Path(raw) / "campaign"), \
                patch.object(canary, "dt", historical_clock), \
                patch.object(canary, "validate_manifest",
                             return_value=(self.parent, self.stage)), \
                patch.object(canary, "validate_approval"), \
                patch.object(canary, "linux_root", return_value="/mnt/c/repo"), \
                patch.object(canary, "preflight", return_value=proof), \
                patch.object(canary, "os", types.SimpleNamespace(name="nt")), \
                patch.object(canary.subprocess, "run", return_value=response) as run:
            state = canary.run_campaign()
            self.assertEqual("blocked", state["status"])
            self.assertEqual(1, state["total_provider_calls"])
            self.assertEqual(0.2, state["total_cost_usd"])
            self.assertEqual("terminal-failed", state["rows"][0]["state"])
            self.assertEqual(1, run.call_count)
            with self.assertRaises(canary.CanaryError):
                canary.run_campaign()


if __name__ == "__main__":
    unittest.main()
