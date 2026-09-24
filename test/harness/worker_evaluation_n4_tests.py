#!/usr/bin/env python3
"""Provider-free N4 miniature: freeze, replay, grading and fault paths."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_evaluation as campaign  # noqa: E402


def _assessment():
    return {"task_kind": "implementation", "complexity": "routine",
            "verification": "executable", "context_tokens": 1000,
            "deadline_seconds": None, "failure_cause": "none",
            "prior_local_repairs": 0, "frame_confidence": "clear",
            "required_artefacts": ["app.py"],
            "evidence": [{"source": "operator", "reference": "issue",
                          "claim": "compute doubles an integer"}]}


def corpus_at(path: Path):
    tasks = []
    for number, split in ((1, "development"), (2, "reserved")):
        ident = f"C{number:02}"
        base = path / ident
        actor = base / "actor"
        actor.mkdir(parents=True)
        (actor / "app.py").write_text(
            "import json, sys\ndef compute(x):\n    return 0\n"
            "if __name__ == '__main__':\n    print(json.dumps(compute(json.loads(sys.stdin.readline()))))\n",
            encoding="utf-8")
        (actor / "public_check.py").write_text(
            "from app import compute\nassert compute(1) == 2\n", encoding="utf-8")
        (base / "issue.md").write_text("Repair compute(x) so it doubles integers.\n", encoding="utf-8")
        (base / "acceptance.json").write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["public check passes"],
            "constraints": [], "required_outputs": ["app.py"],
            "protected_paths": ["public_check.py"],
            "command": [sys.executable, "public_check.py"], "timeout_s": 10}), encoding="utf-8")
        (base / "oracle.json").write_text(json.dumps({"schema_version": 1,
            "cases": [{"input": x, "expected": 2*x, "weight": 1,
                       "milestone": f"double {x}", "critical": False}
                      for x in (-3, 0, 2, 11)]}), encoding="utf-8")
        tasks.append({"id": ident, "family": "configuration", "split": split,
                      "actor": f"{ident}/actor", "issue": f"{ident}/issue.md",
                      "acceptance": f"{ident}/acceptance.json", "oracle": f"{ident}/oracle.json",
                      "allowed_edits": ["app.py"], "assessment": _assessment()})
    (path / "catalogue.json").write_text(json.dumps({"schema_version": 1,
                                                      "tasks": tasks}), encoding="utf-8")


class FakeAdapter:
    offline_fake = True
    calls = 0
    mode = "normal"

    def capability(self, root):
        return {"actor_root": str(root.resolve()), "configured": True,
                "supported_cells": ["worker-sonnet-low", "worker-opus-high"],
                "budget_enforced": True}

    def run(self, request):
        type(self).calls += 1
        if type(self).mode == "normal":
            # The fixture factory injects a case-specific edit, rather than
            # putting a corpus label in the actor's path or worker prompt.
            source = ("import json, sys\n" + self.patch_source +
                      "if __name__ == '__main__':\n    print(json.dumps(compute(json.loads(sys.stdin.readline()))))\n")
            (request.actor_root / "app.py").write_text(source, encoding="utf-8")
        receipt = {"admission_token": request.admission_token,
                   "invocation_id": request.invocation_id, "revision_id": request.revision_id,
                   "decision_digest": request.decision_digest,
                   "intent_digest": request.intent_digest,
                   "requested_cell": request.requested_cell,
                   "actual_model": ("claude-opus-5" if request.requested_cell == "worker-opus-high"
                                    else "claude-sonnet-5"),
                   "identity_valid": True, "child_models": [],
                   "effort_evidence": ("cli-argument:high" if request.requested_cell == "worker-opus-high"
                                       else "cli-argument:low"),
                   "status": "completed", "terminal": True, "writer_stopped": True,
                   "cost_usd": 0.05, "usage": {"cost_usd": 0.05,
                                             "currency": "USD", "cost_source": "provider_reported"}}
        if type(self).mode == "ambiguous":
            receipt.update(status="interrupted", terminal=False, writer_stopped=False,
                           cost_usd=None, usage={"cost_usd": None,
                                                 "currency": None, "cost_source": "unknown"})
        return receipt


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="worker-n4-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        self.corpus.mkdir()
        corpus_at(self.corpus)
        self.manifest = campaign.freeze(self.corpus, miniature=True)
        self.output = self.root / "runs"
        FakeAdapter.calls = 0
        FakeAdapter.mode = "normal"

    @staticmethod
    def factory(actor):
        fake = FakeAdapter()
        fake.patch_source = ("def compute(x):\n    return 2*x\n" if FakeAdapter.calls == 0
                             else "def compute(x):\n    return 2\n")
        return fake

    def test_manifest_freezes_all_inputs_and_rejects_symlinks(self):
        campaign.validate_manifest(self.corpus, self.manifest)
        self.assertEqual(2, len(self.manifest["tasks"]))
        self.assertIn("tools/task_executor.py", self.manifest["bound_source"])
        self.assertIn("C02/oracle.json", self.manifest["corpus_files"])
        with self.assertRaises(campaign.CampaignError):
            campaign.load_catalogue(self.corpus)
        (self.corpus / "C02" / "oracle.json").write_text("tampered", encoding="utf-8")
        with self.assertRaises(campaign.CampaignError):
            campaign.validate_manifest(self.corpus, self.manifest)

    def test_replay_zero_new_calls_and_independent_partial_grade(self):
        runner = campaign.OfflineCampaign(self.corpus, self.manifest, self.output, self.factory)
        state = runner.run()
        self.assertEqual("complete", state["status"])
        self.assertEqual(2, FakeAdapter.calls)
        self.assertEqual([True, False], [row["grade"]["acceptance"] for row in state["results"]])
        self.assertEqual(["accepted", "accepted"], [row["root_state"] for row in state["results"]])
        self.assertTrue(state["results"][1]["grade"]["false_success"])
        self.assertEqual(state, runner.run())
        self.assertEqual(2, FakeAdapter.calls)
        self.assertFalse(list(self.output.rglob("oracle.json")))

    def test_ambiguous_receipt_blocks_campaign_without_replay(self):
        FakeAdapter.mode = "ambiguous"
        runner = campaign.OfflineCampaign(self.corpus, self.manifest, self.output, self.factory)
        result = runner.run()
        self.assertEqual("blocked", result["status"])
        self.assertEqual("uncertain", result["block"]["root_state"])
        self.assertEqual(1, FakeAdapter.calls)
        self.assertEqual("blocked", runner.run()["status"])
        self.assertEqual(1, FakeAdapter.calls)

    def test_concurrent_start_has_one_owner(self):
        runner = campaign.OfflineCampaign(self.corpus, self.manifest, self.output, self.factory)
        results = []
        errors = []
        def start():
            try:
                results.append(runner.run())
            except Exception as exc:
                errors.append(exc)
        threads = [threading.Thread(target=start) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(errors)
        self.assertEqual(2, len(results))
        self.assertEqual(2, FakeAdapter.calls)
        self.assertTrue(all(item["status"] == "complete" for item in results))


if __name__ == "__main__":
    unittest.main()
