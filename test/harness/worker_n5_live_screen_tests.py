#!/usr/bin/env python3
"""Provider-free crash, identity and accounting checks for the N5 driver."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import model_registry  # noqa: E402
import worker_n5_live_screen as live  # noqa: E402
import worker_n5_screen as plan  # noqa: E402


class FakeAdapter:
    offline_fake = True

    def __init__(self, *, mismatch_first=False, raise_first=False,
                 tamper_first=False, first_cost=0.01, receipt_fault=None):
        self.calls = []
        self.mismatch_first = mismatch_first
        self.raise_first = raise_first
        self.tamper_first = tamper_first
        self.first_cost = first_cost
        self.receipt_fault = receipt_fault

    def run(self, request):
        self.calls.append(request)
        if self.raise_first and len(self.calls) == 1:
            raise RuntimeError("simulated ambiguous provider stop")
        if self.tamper_first and len(self.calls) == 1:
            (request.actor_root / "acceptance.json").write_text("{}\n", encoding="utf-8")
        matched = not (self.mismatch_first and len(self.calls) == 1)
        model = model_registry.resolve_cell(request.requested_cell)["expected_provider_model"]
        receipt = {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "requested_effort": model_registry.resolve_cell(request.requested_cell)["effort"],
                "served_effort": None, "actual_model": model if matched else "unexpected",
                "child_models": [], "identity_valid": True,
                "status": "completed" if matched else "failed",
                "terminal": True, "writer_stopped": True,
                "cost_usd": self.first_cost if len(self.calls) == 1 else 0.01,
                "usage": {"input_tokens": 1, "output_tokens": 1,
                          "cache_creation_input_tokens": 0,
                          "cache_read_input_tokens": 0}, "wall_clock_s": 0.01}
        if len(self.calls) == 1 and self.receipt_fault == "wrong_intent":
            receipt["intent_digest"] = "0" * 64
        if len(self.calls) == 1 and self.receipt_fault == "unknown_cost":
            receipt.update(terminal=False, writer_stopped=False, cost_usd=None,
                           status="interrupted")
        return receipt


class LiveScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = plan.build_manifest(credential_method="api_key",
                                           host_attestation_sha256="a" * 64,
                                           spend_notice_sha256="b" * 64)
        cls.approval = {"schema_version": 1, "decision": "approved",
                        "manifest_sha256": cls.manifest["manifest_sha256"],
                        "maximum_authorised_usd": 48.75,
                        "credential_method": "api_key",
                        "spend_notice_sha256": "b" * 64,
                        "approved_by": "synthetic-test", "approved_at": "2026-09-24T00:00:00Z"}

    @staticmethod
    def grade(actor, oracle, oracle_sha, app_sha, root_state):
        return {"acceptance": False, "quality": 20,
                "critical_error": False, "false_success": False,
                "oracle_sha256": oracle_sha, "actor_app_sha256": app_sha,
                "case_count": 1, "milestones": []}

    def runner(self, output, adapter, grader=None):
        return live.LiveScreen(self.manifest, self.approval, output, adapter=adapter,
                               grader=grader or self.grade, check_host=False)

    def test_full_schedule_and_budget_without_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeAdapter()
            result = self.runner(Path(directory) / "run", fake).run()
            self.assertEqual("complete", result["status"])
            self.assertEqual(60, len(fake.calls))
            self.assertEqual(60, len(result["rows"]))
            self.assertEqual(15, sum(row["task"] == "I00" for row in result["rows"]))
            self.assertEqual(45, sum(row["grade"] is not None for row in result["rows"]))
            self.assertFalse(result["stopped_cells"])
            budget = json.loads((Path(directory) / "run" / "budget.json").read_text())
            self.assertEqual(60, len(budget["invocations"]))
            self.assertTrue(all(row["state"] == "settled"
                                for row in budget["invocations"].values()))
            self.assertEqual("complete", self.runner(Path(directory) / "run", fake).run()["status"])
            self.assertEqual(60, len(fake.calls))

    def test_default_production_path_is_closed_until_credential_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(live.LiveScreenError, "credential delivery"):
                live.LiveScreen(self.manifest, self.approval, Path(directory) / "run",
                                check_host=False)
            self.assertFalse((Path(directory) / "run").exists())

    def test_mismatched_identity_skips_only_its_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeAdapter(mismatch_first=True)
            result = self.runner(Path(directory) / "run", fake).run()
            self.assertEqual("complete", result["status"])
            self.assertEqual(57, len(fake.calls))
            self.assertEqual(["stopped", "skipped", "skipped", "skipped"],
                             [row["status"] for row in result["rows"][:4]])
            self.assertEqual(1, len(result["stopped_cells"]))

    def test_ambiguous_exception_retains_charge_and_never_replays(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeAdapter(raise_first=True)
            result = self.runner(Path(directory) / "run", fake).run()
            self.assertEqual("blocked", result["status"])
            self.assertEqual(1, len(fake.calls))
            self.assertEqual("blocked", self.runner(Path(directory) / "run", fake).run()["status"])
            self.assertEqual(1, len(fake.calls))
            budget = json.loads((Path(directory) / "run" / "budget.json").read_text())
            self.assertEqual("uncertain", next(iter(budget["invocations"].values()))["state"])

    def test_unmatched_or_incomplete_receipt_retains_hold(self):
        for fault in ("wrong_intent", "unknown_cost"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                fake = FakeAdapter(receipt_fault=fault)
                output = Path(directory) / "run"
                self.assertEqual("blocked", self.runner(output, fake).run()["status"])
                self.assertEqual("blocked", self.runner(output, fake).run()["status"])
                self.assertEqual(1, len(fake.calls))
                budget = json.loads((output / "budget.json").read_text())
                self.assertEqual(1, len(budget["invocations"]))
                self.assertNotEqual("settled", next(iter(budget["invocations"].values()))
                                    ["state"])

    def test_durable_receipt_resumes_grading_without_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeAdapter()
            attempts = 0

            def flaky_grade(*args):
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    raise RuntimeError("simulated grader interruption")
                return self.grade(*args)

            output = Path(directory) / "run"
            with self.assertRaisesRegex(RuntimeError, "grader interruption"):
                self.runner(output, fake, flaky_grade).run()
            self.assertEqual(2, len(fake.calls))
            result = self.runner(output, fake, flaky_grade).run()
            self.assertEqual("complete", result["status"])
            self.assertEqual(60, len(fake.calls))
            self.assertEqual(46, attempts)

    def test_protected_edit_and_budget_breach_fail_closed(self):
        for fake in (FakeAdapter(tamper_first=True), FakeAdapter(first_cost=50.0)):
            with self.subTest(fake=vars(fake)), tempfile.TemporaryDirectory() as directory:
                result = self.runner(Path(directory) / "run", fake).run()
                self.assertEqual("blocked", result["status"])
                self.assertEqual(1, len(fake.calls))
                self.assertTrue(json.loads((Path(directory) / "run" / "budget.json").read_text())
                                ["cancelled"])

    def test_unbound_grade_blocks_after_receipt_without_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeAdapter()

            def unbound_grade(*args):
                return {**self.grade(*args), "oracle_sha256": "0" * 64}

            output = Path(directory) / "run"
            result = self.runner(output, fake, unbound_grade).run()
            self.assertEqual("blocked", result["status"])
            self.assertEqual(2, len(fake.calls))
            self.assertEqual("blocked", self.runner(output, fake, unbound_grade).run()["status"])
            self.assertEqual(2, len(fake.calls))


if __name__ == "__main__":
    unittest.main()
