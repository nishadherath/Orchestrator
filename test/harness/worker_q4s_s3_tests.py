"""Provider-free S3 checks for terminal failures and the head-only scope."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_q4s_admission as journal  # noqa: E402
import worker_q4s_canary_live as canary  # noqa: E402
from worker_adapter import digest  # noqa: E402
from worker_q4r_structured import report_schema  # noqa: E402


class Q4SS3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = json.loads(canary.screen.MANIFEST.read_text(encoding="utf-8"))
        cls.stage = json.loads(canary.MANIFEST.read_text(encoding="utf-8"))

    def episode(self, *, eligible: bool = True, amount: float = 0.5) -> dict:
        cell = canary.CELLS[0]
        model = "claude-sonnet-5"
        actor = self.parent["canary"]
        return {
            "task_id": "Q4S-CANARY", "episode_label": cell,
            "parent_manifest_sha256": self.parent["manifest_sha256"],
            "stage_manifest_sha256": self.stage["manifest_sha256"],
            "settlement": {"charged_usd": amount, "provider_calls": 1,
                           "writer_stopped": True, "cost_settled": True},
            "qualification_eligible": eligible,
            "receipt": {"requested_cell": cell, "actual_model": model,
                        "root_models": [model], "status": "completed",
                        "terminal": True, "writer_stopped": True,
                        "identity_valid": True, "report_observability": "present",
                        "boundary": {"changed_paths": [actor["editable_paths"][0]],
                                     "q1_record_sha256": "a" * 64,
                                     "q1_spec_sha256": "b" * 64},
                        "transport": {"mode": "claude-code-json-schema-v1",
                                      "schema_sha256": digest(report_schema()),
                                      "structured_output_present": True}},
            "protected_sha256": {name: value for name, value in
                                 actor["actor_files"].items()
                                 if name not in actor["editable_paths"]},
            "snapshot": {"files": {}},
            "executable_grade": {"isolated": True, "public_pass": False},
            "quality_v2": {"scored": False},
        }

    def test_manifest_binds_driver_and_exact_two_call_scope(self):
        with patch.object(canary, "frozen_parent", return_value=self.parent):
            self.assertEqual(self.stage, canary.build_manifest())
        self.assertEqual(2, self.stage["maximum_provider_calls"])
        self.assertEqual([], self.stage["repair_cells"])

    def test_missing_report_is_settled_failure_without_second_call(self):
        episode = self.episode(eligible=False)
        episode["receipt"]["report_observability"] = "absent"
        episode["receipt"]["transport"]["structured_output_present"] = False
        canary.validate_episode(episode, canary.CELLS[0], self.parent, self.stage)
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
            journal.mark_intent(path, 1, "Q4S-CANARY", canary.CELLS[0])
            state = journal.settle_episode(path, episode)
            self.assertEqual("blocked", state["status"])
            self.assertEqual(1, state["total_provider_calls"])
            self.assertEqual(0.5, state["total_cost_usd"])
            with self.assertRaises(journal.Q4SAdmissionError):
                journal.mark_intent(path, 2, "Q4S-CANARY", canary.CELLS[1])

    def test_overrun_and_false_success_are_rejected(self):
        overrun = self.episode(eligible=False, amount=3.01)
        canary.validate_episode(overrun, canary.CELLS[0], self.parent, self.stage)
        forged = self.episode(eligible=True)
        forged["receipt"]["root_models"] = ["claude-opus-5"]
        with self.assertRaises(canary.CanaryError):
            canary.validate_episode(forged, canary.CELLS[0], self.parent,
                                    self.stage)


if __name__ == "__main__":
    unittest.main()
