#!/usr/bin/env python3
"""Provider-free checks for the frozen Q4R screen and paid admission gate."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_q4r_screen as plan  # noqa: E402
import worker_q4r_screen_live as live  # noqa: E402
import model_registry  # noqa: E402
from worker_adapter import digest  # noqa: E402
from worker_q3_public_catalogue import sha  # noqa: E402


class Q4RScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(plan.MANIFEST.read_text(encoding="utf-8"))

    def test_twelve_rows_are_source_bound_and_reserved_work_is_excluded(self):
        manifest = self.manifest
        self.assertEqual(digest({key: value for key, value in manifest.items()
                                 if key != "manifest_sha256"}),
                         manifest["manifest_sha256"])
        self.assertEqual(12, len(manifest["rows"]))
        self.assertEqual(36, manifest["cost"]["maximum_provider_calls"])
        self.assertEqual(72.0, manifest["cost"]["combined_allocation_usd"])
        self.assertFalse(manifest["reserved_tasks_allowed"])
        self.assertFalse(manifest["controller_allowed"])
        self.assertEqual(sha(plan.TRIGGERS), manifest["public_trigger_sha256"])
        self.assertEqual(sha(plan.NOTICE), manifest["spend_notice_sha256"])
        self.assertEqual({"P04", "P05", "P06", "P08"},
                         {row["task_id"] for row in manifest["rows"]})
        for task in plan.TASKS:
            rows = [row for row in manifest["rows"] if row["task_id"] == task]
            self.assertEqual(set(plan.LABELS),
                             {row["episode_label"] for row in rows})
            self.assertTrue(all(row["trigger"]["triggered"] for row in rows))
            self.assertTrue(all(row["ladder"][1:] == plan.REPAIR_TAIL
                                for row in rows))

    def test_only_exact_operator_approval_is_accepted(self):
        manifest = self.manifest
        approval = {"schema_version": 1, "decision": "approved",
                    "manifest_sha256": manifest["manifest_sha256"],
                    "maximum_authorised_usd": 72.0,
                    "maximum_provider_calls": 36,
                    "spend_notice_sha256": manifest["spend_notice_sha256"],
                    "credential_method": "claude-code-wsl-subscription",
                    "approved_by": "operator", "approved_at": "2026-09-25T18:00:00Z"}
        plan.validate_approval(manifest, approval)
        for key, value in (("manifest_sha256", "0" * 64),
                           ("maximum_authorised_usd", 73.0),
                           ("credential_method", "api-key")):
            changed = {**approval, key: value}
            with self.subTest(key=key), self.assertRaises(plan.ScreenError):
                plan.validate_approval(manifest, changed)
        if plan.APPROVAL.exists():
            plan.validate_approval(manifest, json.loads(plan.APPROVAL.read_text(
                encoding="utf-8")))

    def test_decision_retains_b0_when_candidate_cost_exceeds_guard(self):
        rows = []
        for item in self.manifest["rows"]:
            label = item["episode_label"]
            quality = {"hidden_accepted": label == "sonnet-high",
                       "quality": 90 if label == "sonnet-high" else 70,
                       "critical_error": False,
                       "unsupported_completion": False,
                       "report_observability": "present"}
            rows.append({"state": "graded", "episode": {
                "task_id": item["task_id"], "episode_label": label,
                "quality_v2": quality,
                "budget": {"spent_usd": 0.9 if label == "sonnet-high" else 0.3},
                "attempts": [{}],
            }})
        decision = live.analyse({"rows": rows}, self.manifest)
        self.assertEqual("retain-b0", decision["policy_decision"])
        self.assertIsNone(decision["selected_candidate"])
        self.assertFalse(decision["candidates"][0]["qualifies"])
        for row in rows:
            if row["episode"]["episode_label"] == "sonnet-high":
                row["episode"]["budget"]["spent_usd"] = 0.4
        decision = live.analyse({"rows": rows}, self.manifest)
        self.assertEqual("provisional-candidate", decision["policy_decision"])
        self.assertEqual("sonnet-high", decision["selected_candidate"])

    def test_attempt_rejects_missing_structured_output_evidence(self):
        row = self.manifest["rows"][0]
        report = {"binding": {"requested_cell": row["first_cell"]}}
        quality = {"task_sha256": row["task_sha256"], "inconclusive": False}
        quality["grade_sha256"] = digest(quality)
        snapshot = {"schema_version": 1, "files": {},
                    "sequence": row["sequence"], "task_id": row["task_id"],
                    "episode_label": row["episode_label"]}
        snapshot["snapshot_sha256"] = digest(snapshot)
        attempt = {"terminal": True, "writer_stopped": True,
                   "identity_valid": True, "requested_cell": row["first_cell"],
            "actual_model": model_registry.resolve_cell(
                "worker-sonnet-high")["cli_model"],
                   "requested_effort": "low", "cost_usd": 0.1,
                   "q1_record_sha256": "a" * 64, "q1_spec_sha256": "b" * 64,
                   "evaluation_report": report,
                   "evaluation_report_digest": digest(report),
                   "evaluation_transport": {"mode": "claude-code-json-schema-v1",
                      "schema_sha256": self.manifest["schema_sha256"],
                      "structured_output_present": False}}
        receipt = {"task_id": row["task_id"],
                   "episode_label": row["episode_label"], "root_state": "accepted",
                   "budget": {"unresolved": False, "spent_usd": 0.1},
                   "attempts": [attempt], "quality_v2": quality,
                   "executable_grade": {
                       "task_sha256": row["source_task_sha256"],
                       "oracle_sha256": row["oracle_sha256"],
                       "case_source_sha256": row["case_source_sha256"],
                       "oracle_read_denied": True,
                       "source_workspace_unchanged": True,
                       "provider_calls": 0},
                   "protected_sha256": {name: value for name, value in
                       row["actor_files"].items() if name not in row["editable_paths"]},
                   "snapshot": snapshot}
        with self.assertRaises(live.LiveScreenError):
            live.validate_receipt(row, receipt)


if __name__ == "__main__":
    unittest.main()
