#!/usr/bin/env python3
"""Provider-free N5 development admission and no-replay campaign checks."""
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
import acceptance  # noqa: E402
import worker_n5_development as plan  # noqa: E402
from worker_n5_corpus import REFERENCE  # noqa: E402
from worker_n5_live_development import LiveDevelopment, LiveDevelopmentError  # noqa: E402
from worker_adapter import digest  # noqa: E402


class FourCallAdapter:
    offline_fake = True

    def __init__(self):
        self.calls = []

    def capability(self, actor):
        return {"actor_root": str(actor.resolve()), "enforcement_proven": False,
                "budget_enforced": True, "supported_cells": plan.supported_cells(model_registry.load())}

    def run(self, request):
        self.calls.append(request)
        uncertain = len(self.calls) == 4
        if not uncertain:
            (request.actor_root / "app.py").write_text(REFERENCE, encoding="utf-8")
        cell = model_registry.resolve_cell(request.requested_cell)
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": cell["expected_provider_model"],
                "identity_valid": True, "child_models": [],
                "status": "interrupted" if uncertain else "completed",
                "terminal": not uncertain, "writer_stopped": not uncertain,
                "cost_usd": None if uncertain else 0.2,
                "usage": {"cost_usd": None if uncertain else 0.2},
                "effort_evidence": f"cli-argument:{cell['effort']}",
                "started_at": "2026-09-25T00:00:00Z",
                "finished_at": "2026-09-25T00:00:01Z", "wall_clock_s": 1.0}


def command_runner(argv, **kwargs):
    result = subprocess.run([sys.executable, *argv[1:]], **kwargs)
    contract = json.loads((kwargs["cwd"] / "acceptance.json").read_text())
    proof = {"mode": "offline-fake",
             "artefacts_digest": acceptance.snapshot(
                 kwargs["cwd"], contract["required_outputs"])["digest"],
             "protected_digest": acceptance.snapshot(
                 kwargs["cwd"], contract["protected_paths"])["digest"]}
    result.isolation_evidence = {**proof, "sha256": digest(proof)}
    return result


def grader(actor, oracle, oracle_sha, app_sha, root_state):
    return {"oracle_sha256": oracle_sha, "actor_app_sha256": app_sha,
            "acceptance": root_state == "accepted", "quality": 100.0,
            "critical_error": False, "false_success": False,
            "case_count": 1, "milestones": ["offline fake"]}


class DevelopmentTests(unittest.TestCase):
    def manifest(self):
        manifest = plan.build_manifest(
            host_attestation_sha256="a" * 64,
            subscription_attestation_sha256="b" * 64,
            subscription_sentinel_sha256="c" * 64,
            spend_notice_sha256="d" * 64)
        plan.validate_manifest(manifest, check_host=False)
        return manifest

    @staticmethod
    def approval(manifest):
        return {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_authorised_usd": plan.CAMPAIGN_CEILING_USD,
                "credential_method": "subscription",
                "spend_notice_sha256": manifest["spend_notice_sha256"],
                "approved_by": "offline-test", "approved_at": "2026-09-25T00:00:00Z"}

    def test_schedule_is_public_balanced_and_authorisation_exact(self):
        manifest = self.manifest()
        self.assertEqual(36, len(manifest["rows"]))
        self.assertEqual(["B0", "candidate", "alternative"],
                         [row["arm"] for row in manifest["rows"][:3]])
        self.assertEqual(["candidate", "alternative", "B0"],
                         [row["arm"] for row in manifest["rows"][3:6]])
        self.assertEqual({"worker-sonnet-low", "worker-sonnet-high", "worker-opus-high"},
                         {row["selected_cell"] for row in manifest["rows"]
                          if row["arm"] == "candidate"})
        self.assertTrue(all(row["task_id"].startswith("D") for row in manifest["rows"]))
        plan.validate_authorisation(manifest, self.approval(manifest), check_host=False)
        for change in ({"decision": "pending"}, {"maximum_authorised_usd": 109.0}):
            with self.assertRaises(plan.DevelopmentError):
                plan.validate_authorisation(manifest,
                                            {**self.approval(manifest), **change},
                                            check_host=False)
        with self.assertRaises(plan.DevelopmentError):
            plan.validate_manifest({**manifest, "rows": manifest["rows"][:-1]},
                                   check_host=False)

    def test_started_uncertain_episode_blocks_without_replay(self):
        manifest = self.manifest()
        adapter = FourCallAdapter()
        with tempfile.TemporaryDirectory(prefix="worker-n5-development-") as tmp:
            campaign = LiveDevelopment(manifest, self.approval(manifest), Path(tmp),
                                       adapter=adapter, grader=grader,
                                       command_runner=command_runner, check_host=False)
            result = campaign.run()
            self.assertEqual("blocked", result["status"])
            self.assertEqual(3, len(result["rows"]))
            self.assertEqual(["B0", "candidate", "alternative"],
                             [row["arm"] for row in result["rows"]])
            self.assertTrue(all(row["root_state"] == "accepted"
                                for row in result["rows"]))
            self.assertEqual("candidate", manifest["rows"][3]["arm"])
            self.assertEqual(["worker-sonnet-low", "worker-sonnet-low",
                              "worker-sonnet-medium", "worker-sonnet-low"],
                             [call.requested_cell for call in adapter.calls])
            self.assertEqual(4, len(adapter.calls))
            self.assertEqual("blocked", campaign.run()["status"])
            self.assertEqual(4, len(adapter.calls))
            ledger = json.loads((Path(tmp) / "budget.json").read_text())
            self.assertEqual(3, sum(row["state"] == "settled" for row in
                                    ledger["invocations"].values()))
            self.assertEqual(1, sum(row["state"] != "settled" for row in
                                    ledger["invocations"].values()))
            budget_path = Path(tmp) / "budget.json"
            budget_bytes = budget_path.read_bytes()
            budget_path.unlink()
            with self.assertRaisesRegex(LiveDevelopmentError, "budget is missing"):
                campaign.run()
            budget_path.write_bytes(budget_bytes)
            checkpoint = Path(tmp) / "campaign.json"
            state = json.loads(checkpoint.read_text(encoding="utf-8"))
            state["rows"][0]["arm"] = "alternative"
            state["state_sha256"] = digest({key: value for key, value in state.items()
                                             if key != "state_sha256"})
            checkpoint.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(LiveDevelopmentError, "frozen row"):
                campaign.run()


if __name__ == "__main__":
    unittest.main()
