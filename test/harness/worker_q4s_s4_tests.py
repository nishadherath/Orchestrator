"""Provider-free S4 checks for receipt classification and frozen policy math."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_q4s_screen_live as live  # noqa: E402
from worker_adapter import digest  # noqa: E402
from worker_q4r_structured import report_schema  # noqa: E402
from worker_quality_v2 import report_evidence  # noqa: E402


class Q4SS4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = json.loads(live.screen.MANIFEST.read_text(encoding="utf-8"))
        cls.stage = {"manifest_sha256": "a" * 64}

    def episode(self, row: dict, *, amount: float = 0.2,
                observable: str = "present") -> dict:
        cell = row["first_cell"]
        resolved = live.model_registry.resolve_cell(cell)
        quality = {"task_sha256": live.live_rubric(row)["task_sha256"],
                   "quality": 80, "hidden_accepted": False,
                   "critical_error": False, "unsupported_completion": False,
                   "report_observability": observable, "inconclusive": False}
        quality["grade_sha256"] = digest(quality)
        snapshot = {"files": {}}
        snapshot["snapshot_sha256"] = digest(snapshot)
        report = {"observability": observable}
        attempt = {"requested_cell": cell, "actual_model": resolved["cli_model"],
                   "requested_effort": resolved["effort"],
                   "identity_valid": True, "terminal": True,
                   "writer_stopped": True, "cost_usd": amount,
                   "q1_record_sha256": "b" * 64,
                   "q1_spec_sha256": "c" * 64, "changed_paths": [],
                   "evaluation_report": report,
                   "evaluation_report_digest": digest(report),
                   "evaluation_transport": {
                       "mode": "claude-code-json-schema-v1",
                       "schema_sha256": digest(report_schema())}}
        return {"sequence": row["sequence"], "task_id": row["task_id"],
                "episode_label": row["episode_label"],
                "parent_manifest_sha256": self.parent["manifest_sha256"],
                "stage_manifest_sha256": self.stage["manifest_sha256"],
                "root_state": "partial", "budget": {"spent_usd": amount},
                "attempts": [attempt],
                "settlement": {"charged_usd": amount, "provider_calls": 1,
                               "cost_settled": True, "writer_stopped": True},
                "quality_v2": quality,
                "executable_grade": {
                    "task_sha256": row["source_task_sha256"],
                    "oracle_sha256": row["oracle_sha256"],
                    "case_source_sha256": row["case_source_sha256"],
                    "source_workspace_unchanged": True, "public_isolated": True},
                "protected_sha256": {name: value for name, value in
                                     row["actor_files"].items()
                                     if name not in row["editable_paths"]},
                "snapshot": snapshot}

    def test_coordinator_rejects_nested_wsl_launch_before_preflight(self):
        with patch.object(live, "os", types.SimpleNamespace(name="posix")):
            with self.assertRaisesRegex(live.ScreenError, "requires Windows"):
                live.run_campaign()

    def test_terminal_missing_report_is_scored_without_stopping(self):
        row = self.parent["rows"][0]
        episode = self.episode(row, observable="worker-missing")
        self.assertIsNone(live.validate_receipt(row, episode, self.parent, self.stage))
        with tempfile.TemporaryDirectory() as raw, patch.object(live, "RUN", Path(raw)):
            intent = {"sequence": row["sequence"], "task_id": row["task_id"],
                      "episode_label": row["episode_label"],
                      "state": "provider-call-may-start"}
            live.journal._write(Path(raw) / "campaign.json", {
                "status": "running", "rows": [intent],
                "total_cost_usd": 0, "total_provider_calls": 0})
            state = live.settle_campaign_episode(episode, None)
            self.assertEqual("running", state["status"])
            self.assertEqual("graded", state["rows"][0]["state"])
            self.assertEqual(1, state["total_provider_calls"])

    def test_overrun_and_identity_mismatch_stop_after_settlement(self):
        row = self.parent["rows"][0]
        overrun = self.episode(row, amount=4.01)
        self.assertEqual("settled episode allocation overrun",
                         live.validate_receipt(row, overrun, self.parent, self.stage))
        wrong = self.episode(row)
        wrong["attempts"][0]["actual_model"] = live.model_registry.resolve_cell(
            "worker-opus-high")["cli_model"]
        self.assertEqual("settled model identity mismatch",
                         live.validate_receipt(row, wrong, self.parent, self.stage))
        unknown = self.episode(row)
        unknown["attempts"][0]["cost_usd"] = None
        with self.assertRaises(live.ScreenError):
            live.validate_receipt(row, unknown, self.parent, self.stage)

    def test_policy_uses_negative_b0_and_requires_real_gain(self):
        episodes = [self.episode(row) for row in self.parent["rows"]]
        state = {"status": "complete", "rows": [
            {"state": "graded", "episode": item} for item in episodes]}
        decision = live.analyse(state, self.parent, self.stage)
        self.assertEqual("retain-b0", decision["policy_decision"])
        self.assertEqual(6, decision["summaries"]["policy"]["families"])
        positive = next(item for item in episodes if item["episode_label"] ==
                        "sonnet-medium" and next(row for row in self.parent["rows"]
                                                 if row["task_id"] == item["task_id"]
                                                 )["trigger"]["triggered"])
        positive["quality_v2"].update(hidden_accepted=True, quality=90)
        positive["budget"]["spent_usd"] = 0.3
        positive["attempts"][0]["cost_usd"] = 0.3
        decision = live.analyse(state, self.parent, self.stage)
        self.assertEqual("provisional-candidate", decision["policy_decision"])
        self.assertEqual(0, decision["summaries"]["b0-a"]["hidden_accepted"])
        negative_medium = next(item for item in episodes if item["episode_label"] ==
                               "sonnet-medium" and not next(
                                   row for row in self.parent["rows"]
                                   if row["task_id"] == item["task_id"]
                                   )["trigger"]["triggered"])
        negative_medium["quality_v2"].update(hidden_accepted=True, quality=100)
        self.assertEqual("provisional-candidate",
                         live.analyse(state, self.parent, self.stage)["policy_decision"])
        self.assertEqual(1, live.analyse(state, self.parent, self.stage)["summaries"]
                         ["policy"]["hidden_accepted"])

    def test_reference_overlay_earns_executable_and_report_credit(self):
        row = self.parent["rows"][0]
        source = live.FIXTURES / row["task_id"]
        with tempfile.TemporaryDirectory() as raw:
            actor = Path(raw)
            shutil.copytree(source / "actor", actor, dirs_exist_ok=True)
            shutil.copytree(source / "reference", actor, dirs_exist_ok=True)
            binding = {key: "f" * 64 for key in (
                "invocation_id", "revision_id", "final_revision_sha256",
                "stream_sha256", "prompt_sha256")}
            binding["task_sha256"] = live.live_rubric(row)["task_sha256"]
            binding["requested_cell"] = row["first_cell"]
            report = report_evidence(json.dumps({
                "status": "completed", "diagnosis": "Repaired the stated bug.",
                "evidence": ["Public and hidden behaviour passed."], "checks": [],
                "remaining": [], "clarification": None}), binding)

            def fake_runner(_task):
                def run(*_args, **_kwargs):
                    result = subprocess.CompletedProcess([], 0, b"", b"")
                    result.isolation_evidence = {"test": True}
                    return result
                return run

            fake_adapter = types.SimpleNamespace(isolated_public_runner=fake_runner)
            with patch.dict(sys.modules, {"worker_wsl_q3_adapter": fake_adapter}):
                executable, quality = live.executable_grade(row, actor, "accepted", report)
            self.assertEqual(100, executable["executable_score"])
            self.assertEqual(100, quality["quality"])
            self.assertTrue(quality["hidden_accepted"])


if __name__ == "__main__":
    unittest.main()
