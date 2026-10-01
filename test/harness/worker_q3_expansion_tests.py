#!/usr/bin/env python3
"""Provider-free approval, receipt and no-replay tests for Q3 expansion."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_q3_expansion as plan  # noqa: E402
import worker_q3_expansion_live as live  # noqa: E402
from worker_adapter import digest  # noqa: E402


def sample():
    row = {"sequence": 1, "task_id": "P03", "task_sha256": "a" * 64,
           "oracle_sha256": "b" * 64, "case_source_sha256": "c" * 64,
           "actor_files": {"click/core.py": "d" * 64,
                           "ISSUE.md": "e" * 64},
           "editable_paths": ["click/core.py"],
           "ladder": plan.canary.LADDER, "episode_maximum_usd": 6.0}
    receipt = {"task_id": "P03", "root_state": "partial",
               "budget": {"unresolved": False, "spent_usd": 0.1},
               "attempts": [{"sequence": 1, "requested_cell": "worker-sonnet-low",
                             "requested_effort": "low", "actual_model": "claude-sonnet-5",
                             "identity_valid": True, "terminal": True,
                             "writer_stopped": True, "cost_usd": 0.1,
                             "q1_record_sha256": "d" * 64,
                             "q1_spec_sha256": "e" * 64}],
               "hidden_grade": {"task_sha256": "a" * 64,
                                "task_id": "P03", "root_state": "partial",
                                "oracle_sha256": "b" * 64,
                                "case_source_sha256": "c" * 64,
                                "source_workspace_unchanged": True,
                                "variant": "candidate",
                                "oracle_read_denied": True, "provider_calls": 0},
               "protected_sha256": {"ISSUE.md": "e" * 64}}
    receipt["hidden_grade"]["grade_sha256"] = digest(receipt["hidden_grade"])
    return row, receipt


class ExpansionTests(unittest.TestCase):
    def test_exact_approval_and_allowance(self):
        manifest = {"manifest_sha256": "a" * 64,
                    "spend_notice_sha256": "b" * 64,
                    "credential_method": "claude-code-wsl-subscription"}
        approval = {"schema_version": 1, "decision": "approved",
                    "manifest_sha256": manifest["manifest_sha256"],
                    "maximum_authorised_usd": 36.0,
                    "maximum_provider_calls": 18,
                    "spend_notice_sha256": manifest["spend_notice_sha256"],
                    "credential_method": manifest["credential_method"],
                    "approved_by": "operator-standing-through-Q4-2026-09-25",
                    "approved_at": "2026-09-25T00:00:00Z"}
        plan.validate_approval(manifest, approval)
        for key, wrong in (("manifest_sha256", "f" * 64),
                           ("maximum_authorised_usd", 36.01),
                           ("maximum_provider_calls", 19),
                           ("decision", "approval-requested"),
                           ("approved_by", "unknown")):
            with self.subTest(key=key), self.assertRaises(plan.ExpansionError):
                plan.validate_approval(manifest, {**approval, key: wrong})

    def test_receipt_rejects_identity_isolation_grade_and_cost_drifts(self):
        row, receipt = sample()
        live.validate_receipt(row, receipt)
        mutations = (
            ("attempts", 0, "terminal", False),
            ("attempts", 0, "identity_valid", False),
            ("attempts", 0, "requested_cell", "worker-opus-high"),
            ("attempts", 0, "q1_record_sha256", None),
            ("hidden_grade", None, "oracle_read_denied", False),
            ("hidden_grade", None, "task_sha256", "f" * 64),
            ("protected_sha256", None, "ISSUE.md", "f" * 64),
            ("budget", None, "spent_usd", 6.1),
        )
        for container, index, key, value in mutations:
            changed = copy.deepcopy(receipt)
            target = changed[container] if index is None else changed[container][index]
            target[key] = value
            with self.subTest(key=key), self.assertRaises(live.LiveExpansionError):
                live.validate_receipt(row, changed)

    def test_completed_episode_cannot_be_replayed(self):
        row, receipt = sample()
        manifest = {"manifest_sha256": "f" * 64, "rows": [row],
                    "cost": {"combined_allocation_usd": 36.0,
                             "maximum_provider_calls": 18}}
        with tempfile.TemporaryDirectory(prefix="q3-expansion-test-",
                                         dir=ROOT / "test/results") as raw:
            folder = Path(raw)
            manifest_path = folder / "manifest.json"
            approval_path = folder / "approval.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            approval_path.write_text("{}", encoding="utf-8")
            calls = []

            def fake_provider(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0,
                    stdout=json.dumps({"result": "COMPLETE", "episode": receipt}))

            with (patch.object(plan, "MANIFEST", manifest_path),
                  patch.object(plan, "APPROVAL", approval_path),
                  patch.object(plan, "validate"),
                  patch.object(plan, "validate_approval"),
                  patch.object(live, "RUN", folder / "run"),
                  patch.object(live, "linux_root", return_value="/mnt/c/repo"),
                  patch.object(live.subprocess, "run", side_effect=fake_provider)):
                result = live.run_campaign()
                self.assertEqual(result["status"], "complete")
                self.assertEqual(result["total_provider_calls"], 1)
                with self.assertRaises(live.LiveExpansionError):
                    live.run_campaign()
            self.assertEqual(len(calls), 1)

    def test_uncertain_episode_blocks_replay_and_next_task(self):
        row, _ = sample()
        next_row = {**row, "sequence": 2, "task_id": "P04"}
        manifest = {"manifest_sha256": "f" * 64, "rows": [row, next_row],
                    "cost": {"combined_allocation_usd": 36.0,
                             "maximum_provider_calls": 18}}
        with tempfile.TemporaryDirectory(prefix="q3-uncertain-test-",
                                         dir=ROOT / "test/results") as raw:
            folder = Path(raw)
            manifest_path = folder / "manifest.json"
            approval_path = folder / "approval.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            approval_path.write_text("{}", encoding="utf-8")
            calls = []

            def uncertain(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=124,
                    stdout=json.dumps({"result": "ERROR", "error_type": "TimeoutExpired"}))

            with (patch.object(plan, "MANIFEST", manifest_path),
                  patch.object(plan, "APPROVAL", approval_path),
                  patch.object(plan, "validate"),
                  patch.object(plan, "validate_approval"),
                  patch.object(live, "RUN", folder / "run"),
                  patch.object(live, "linux_root", return_value="/mnt/c/repo"),
                  patch.object(live.subprocess, "run", side_effect=uncertain)):
                result = live.run_campaign()
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["rows"][0]["state"], "uncertain")
                with self.assertRaises(live.LiveExpansionError):
                    live.run_campaign()
            self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
