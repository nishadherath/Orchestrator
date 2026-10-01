"""Forged-evidence and no-replay checks for the prospective Q4T driver."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_adapter import digest  # noqa: E402
from worker_q4r_structured import report_schema  # noqa: E402
from worker_q4t_screen import MANIFEST as PARENT_MANIFEST, live_rubric  # noqa: E402
from worker_q4t_screen_evidence import (  # noqa: E402
    EvidenceError, executable_grade, preserve, validate_episode,
)
from worker_q4t_screen_live import (  # noqa: E402
    MANIFEST, adjudicate_episode, analyse, build_manifest, run_campaign, stop_campaign,
    validate_approval,
)
from worker_q4t_public import actor_root, build, oracle_root  # noqa: E402
from worker_quality_v2 import grade, report_evidence  # noqa: E402


REPORT = {"status": "completed", "diagnosis": "Fixed atomic batches.",
          "evidence": ["The public check passed."], "checks": [],
          "remaining": [], "clarification": None}


class Q4TS3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))
        cls.stage = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.row = next(row for row in cls.parent["rows"]
                       if row["task_id"] == "T07"
                       and row["episode_label"] == "sonnet-medium")

    def episode(self, *, invalid_report=False):
        row = self.row
        task = build("T07")
        oracle = json.loads((oracle_root("T07") / task["oracle_file"]).read_text(
            encoding="utf-8"))
        invocation, revision = "a" * 32, "b" * 64
        after = {name: "c" * 64 for name in row["editable_paths"]}
        binding = {"invocation_id": invocation, "revision_id": revision,
                   "final_revision_sha256": digest(after),
                   "stream_sha256": "d" * 64,
                   "task_sha256": live_rubric(row)["task_sha256"],
                   "prompt_sha256": "e" * 64,
                   "requested_cell": row["first_cell"]}
        report = report_evidence(
            None if invalid_report else json.dumps(REPORT), binding,
            transport_valid=not invalid_report)
        cases = [{"milestone": case["milestone"], "passed": True,
                  "weight": case["weight"], "exit_code": 0}
                 for case in oracle["cases"]]
        executable = {"task_sha256": task["task_sha256"],
                      "oracle_sha256": task["oracle_sha256"],
                      "case_source_sha256": task["case_source_sha256"],
                      "public_pass": True, "public_isolated": True,
                      "source_workspace_unchanged": True,
                      "cases": cases, "executable_score": 100}
        executable["evaluator_sha256"] = digest(executable)
        observations = {predicate["id"]: {"passed": True, "evidence": "case passed"}
                        for predicate in live_rubric(row)["predicates"]}
        quality = grade(live_rubric(row), observations, report,
                        root_state="failed" if invalid_report else "accepted",
                        execution_checks={"python3 -B public_check.py": True},
                        expected_binding=binding)
        attempt = {"sequence": 1, "invocation_id": invocation,
                   "revision_id": revision, "receipt_digest": "f" * 64,
                   "requested_cell": row["first_cell"],
                   "requested_effort": "medium", "served_effort": None,
                   "status": "failed" if invalid_report else "completed",
                   "actual_model": "claude-sonnet-5",
                   "root_models": ["claude-sonnet-5"],
                   "identity_valid": True, "terminal": True,
                   "writer_stopped": True, "cost_usd": 0.2,
                   "usage": {}, "wall_clock_s": 10,
                   "verification": "failed" if invalid_report else "passed",
                   "boundary": {"q1_record_sha256": "1" * 64,
                                "q1_spec_sha256": "2" * 64,
                                "changed_paths": list(row["editable_paths"]),
                                "after_sha256": after},
                   "q4t_launcher_sha256": self.stage["runtime_launcher_sha256"],
                   "evaluation_report": report,
                   "evaluation_report_digest": digest(report),
                   "evaluation_transport": {
                       "mode": self.parent["transport_mode"],
                       "schema_sha256": digest(report_schema()),
                       "structured_retry_limit": 5,
                       "structured_output_present": not invalid_report},
                   "q4t_diagnostics": {
                       "result_subtype": ("error_max_structured_output_retries"
                                          if invalid_report else "success"),
                       "real_root_models": ["claude-sonnet-5"],
                       "invalid_line_count": 0,
                       "returncode": 1 if invalid_report else 0}}
        snapshot = {"schema_version": 1, "sequence": row["sequence"],
                    "task_id": row["task_id"],
                    "episode_label": row["episode_label"],
                    "files": {name: "3" * 64 for name in row["editable_paths"]}}
        snapshot["snapshot_sha256"] = digest(snapshot)
        episode = {"sequence": row["sequence"], "task_id": row["task_id"],
                   "episode_label": row["episode_label"], "root_id": "root",
                   "root_state": "blocked" if invalid_report else "accepted",
                   "budget": {"spent_usd": 0.2, "unresolved": False,
                              "invocations": {invocation: {"state": "settled",
                                                           "cost_usd": 0.2}}},
                   "attempts": [attempt], "workspace": "/unused/test/workspace",
                   "parent_manifest_sha256": self.parent["manifest_sha256"],
                   "stage_manifest_sha256": self.stage["manifest_sha256"],
                   "protected_integrity": True,
                   "settlement": {"charged_usd": 0.2, "provider_calls": 1,
                                  "writer_stopped": True, "cost_settled": True},
                   "qualification_eligible": not invalid_report,
                   "report_observability": report["observability"],
                   "executable_grade": executable, "quality_v2": quality,
                   "snapshot": snapshot,
                   "protected_sha256": {
                       name: value for name, value in row["actor_files"].items()
                       if name not in row["editable_paths"]}}
        episode["evidence_sha256"] = digest(episode)
        return episode

    def test_exact_manifest_approval_and_successful_episode(self):
        self.assertEqual(self.stage, build_manifest(self.stage["date_utc"]))
        validate_approval(self.stage)
        episode = self.episode()
        validate_episode(self.row, episode, self.parent, self.stage)
        self.assertIsNone(adjudicate_episode(self.row, episode, self.parent, self.stage))
        episode["attempts"][0]["root_models"] = ["<synthetic>", "claude-sonnet-5"]
        episode["evidence_sha256"] = digest({
            key: value for key, value in episode.items() if key != "evidence_sha256"})
        validate_episode(self.row, episode, self.parent, self.stage)

    def test_settled_invalid_report_is_scored_without_hidden_acceptance(self):
        episode = self.episode(invalid_report=True)
        self.assertTrue(episode["quality_v2"]["inconclusive"])
        self.assertFalse(episode["quality_v2"]["hidden_accepted"])
        self.assertEqual(0, episode["quality_v2"]["component_scores"]["report"])
        self.assertIsNone(adjudicate_episode(self.row, episode, self.parent, self.stage))

    def test_forged_receipt_ledger_grade_and_snapshot_stop_before_policy(self):
        mutators = [
            lambda x: x["attempts"][0]["evaluation_report"].update(raw_sha256="0" * 64),
            lambda x: x["budget"]["invocations"]["a" * 32].update(cost_usd=0.1),
            lambda x: x["executable_grade"].update(executable_score=0),
            lambda x: x["snapshot"]["files"].update({self.row["editable_paths"][0]: "0" * 64}),
            lambda x: x["protected_sha256"].update({"ISSUE.md": "0" * 64}),
            lambda x: x["attempts"][0]["q4t_diagnostics"].update(
                real_root_models=["claude-opus-5"]),
        ]
        for mutate in mutators:
            with self.subTest(mutate=repr(mutate)):
                episode = copy.deepcopy(self.episode())
                mutate(episode)
                episode["evidence_sha256"] = digest({
                    key: value for key, value in episode.items()
                    if key != "evidence_sha256"})
                with mock.patch("worker_q4t_screen_live.settled_stop_reason") as policy:
                    with self.assertRaises(EvidenceError):
                        adjudicate_episode(self.row, episode, self.parent, self.stage)
                    policy.assert_not_called()

    def test_report_failure_cannot_be_forged_into_hidden_acceptance(self):
        episode = self.episode(invalid_report=True)
        episode["quality_v2"]["hidden_accepted"] = True
        episode["quality_v2"]["grade_sha256"] = digest({
            key: value for key, value in episode["quality_v2"].items()
            if key != "grade_sha256"})
        episode["evidence_sha256"] = digest({
            key: value for key, value in episode.items() if key != "evidence_sha256"})
        with self.assertRaises(EvidenceError):
            validate_episode(self.row, episode, self.parent, self.stage)

    def test_reference_patch_grade_and_saved_snapshot_bytes(self):
        episode = self.episode()
        row = self.row
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            shutil.copytree(actor_root("T07"), workspace)
            shutil.copytree(ROOT / "test/fixtures/worker_q4t_public/T07/reference",
                            workspace, dirs_exist_ok=True)

            def public_runner(*_args, **_kwargs):
                process = subprocess.CompletedProcess([], 0, b"", b"")
                process.isolation_evidence = {"test": True}
                return process

            executable, quality = executable_grade(
                row, workspace, "accepted",
                episode["attempts"][0]["evaluation_report"], public_runner)
            self.assertEqual(100, executable["executable_score"])
            self.assertEqual(100, quality["quality"])
            episode["executable_grade"] = executable
            episode["quality_v2"] = quality
            episode["snapshot"] = preserve(row, workspace, root)
            episode["workspace"] = str(workspace)
            episode["evidence_sha256"] = digest({
                key: value for key, value in episode.items()
                if key != "evidence_sha256"})
            validate_episode(row, episode, self.parent, self.stage, run_dir=root)
            copied = root / "patches" / (
                f"{row['sequence']:02d}-t07-{row['episode_label']}") / row["editable_paths"][0]
            copied.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(EvidenceError, "snapshot bytes"):
                validate_episode(row, episode, self.parent, self.stage, run_dir=root)

    def test_positive_candidate_flag_only_for_positive_medium(self):
        with mock.patch("worker_q4t_screen_live.evidence.validate_episode"):
            with mock.patch("worker_q4t_screen_live.settled_stop_reason") as policy:
                policy.return_value = None
                for row in self.parent["rows"]:
                    adjudicate_episode(row, {}, self.parent, self.stage)
                    self.assertEqual(
                        row["trigger"]["triggered"] and
                        row["episode_label"] == "sonnet-medium",
                        policy.call_args.kwargs["candidate_positive"])

    def test_existing_campaign_stops_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch("worker_q4t_screen_live.RUN", Path(temporary)):
                with mock.patch("worker_q4t_screen_live.linux_root") as root:
                    with self.assertRaisesRegex(RuntimeError, "already exists"):
                        run_campaign()
                    root.assert_not_called()

    def test_expired_auth_blocks_before_provider_intent(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "new-run"

            def start(path, manifest_sha256, _preflight):
                path.mkdir()
                from worker_q4s_admission import _write
                _write(path / "campaign.json", {
                    "schema_version": 1, "manifest_sha256": manifest_sha256,
                    "status": "running", "rows": [], "total_cost_usd": 0.0,
                    "total_provider_calls": 0})

            with (mock.patch("worker_q4t_screen_live.RUN", run_dir),
                  mock.patch("worker_q4t_screen_live.validate_manifest",
                             return_value=(self.parent, self.stage)),
                  mock.patch("worker_q4t_screen_live.validate_approval"),
                  mock.patch("worker_q4t_screen_live.linux_root", return_value="/mnt/repo"),
                  mock.patch("worker_q4t_screen_live.journal.start_campaign",
                             side_effect=start),
                  mock.patch("worker_q4t_screen_live.historical_and_runtime"),
                  mock.patch("worker_q4t_screen_live.canary.provider_free_probe",
                             side_effect=RuntimeError("expired")),
                  mock.patch("worker_q4t_screen_live.journal.mark_intent") as intent):
                state = run_campaign()
            self.assertEqual("blocked", state["status"])
            self.assertEqual([], state["rows"])
            intent.assert_not_called()

    def test_stopped_screen_preserves_partial_quality_and_cost(self):
        episode = self.episode(invalid_report=True)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            from worker_q4s_admission import _write

            _write(root / "campaign.json", {
                "schema_version": 1, "manifest_sha256": self.stage["manifest_sha256"],
                "status": "running", "rows": [{"state": "graded", "episode": episode}],
                "total_cost_usd": 0.2, "total_provider_calls": 1})
            with mock.patch("worker_q4t_screen_live.RUN", root):
                state = stop_campaign("known candidate stop", uncertain=False)
            partial = json.loads((root / "partial-analysis.json").read_text(
                encoding="utf-8"))
            self.assertEqual("blocked", state["status"])
            self.assertEqual(1, partial["settled_episodes"])
            self.assertEqual(100, partial["observations"][0]["executable_score"])
            self.assertEqual("transport-invalid",
                             partial["observations"][0]["report_observability"])
            self.assertEqual(0.2, partial["observations"][0]["charged_usd"])
            self.assertFalse(partial["unresolved_intent"])

    def test_synthetic_only_gain_cannot_qualify_policy(self):
        episodes = []
        for row in self.parent["rows"]:
            quality = {"quality": 70, "hidden_accepted": False,
                       "critical_error": False, "unsupported_completion": False,
                       "report_observability": "present"}
            episodes.append({"task_id": row["task_id"],
                             "episode_label": row["episode_label"],
                             "quality_v2": quality,
                             "settlement": {"charged_usd": 0.2},
                             "attempts": [{}]})
        state = {"status": "complete", "rows": [
            {"state": "graded", "episode": item} for item in episodes]}
        synthetic = next(item for item in episodes
                         if item["task_id"] == "T07"
                         and item["episode_label"] == "sonnet-medium")
        synthetic["quality_v2"] = {**synthetic["quality_v2"],
                                   "quality": 100, "hidden_accepted": True}
        decision = analyse(state, self.parent, self.stage)
        self.assertEqual("retain-b0", decision["policy_decision"])
        self.assertFalse(decision["upstream_gain"])
        upstream = next(item for item in episodes
                        if item["task_id"] == "S02"
                        and item["episode_label"] == "sonnet-medium")
        upstream["quality_v2"] = {**upstream["quality_v2"],
                                  "quality": 80, "hidden_accepted": True}
        decision = analyse(state, self.parent, self.stage)
        self.assertTrue(decision["upstream_gain"])
        self.assertEqual("provisional-candidate", decision["policy_decision"])


if __name__ == "__main__":
    unittest.main()
