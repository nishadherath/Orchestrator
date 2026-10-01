"""Fake-provider proof of a settled accepted public-risk review checkpoint."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_evaluation  # noqa: E402
import controller_public_assessment  # noqa: E402
import controller_x5_first_failure as boundary  # noqa: E402
import controller_x5_public_risk_review as review  # noqa: E402
from task_executor import TaskExecutor  # noqa: E402


FILES = {"acceptance.json", "issue.md", "public_check.py", "output.txt",
         "package/service.py"}


class FakeWorker:
    def __init__(self):
        self.calls = []

    def capability(self, root):
        return {"configured": True, "actor_root": str(root.resolve()),
                "enforcement_proven": False}

    def run(self, request):
        self.calls.append(request)
        (request.actor_root / "output.txt").write_text("accepted", encoding="utf-8")
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": "claude-sonnet-5", "identity_valid": True,
                "child_models": [], "status": "completed", "terminal": True,
                "writer_stopped": True, "cost_usd": 0.1,
                "usage": {"cost_usd": 0.1, "cost_source": "provider_reported",
                          "currency": "USD", "input_tokens": 10,
                          "output_tokens": 10, "cache_creation_input_tokens": 0,
                          "cache_read_input_tokens": 0},
                "effort_evidence": "cli-argument:low",
                "started_at": "2026-09-30T00:00:00Z",
                "finished_at": "2026-09-30T00:00:01Z", "wall_clock_s": 1.0}


class PublicRiskReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="x5-public-risk-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.actor = self.base / "producer"
        self.actor.mkdir()
        self.quote = "Public checks cover the nominal output only."
        (self.actor / "issue.md").write_text(
            "Review the output. " + self.quote + "\n", encoding="utf-8")
        (self.actor / "public_check.py").write_text(
            "from pathlib import Path\n"
            "assert Path('output.txt').read_text() == 'accepted'\n",
            encoding="utf-8")
        (self.actor / "output.txt").write_text("wrong", encoding="utf-8")
        (self.actor / "package").mkdir()
        (self.actor / "package/service.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.actor / "acceptance.json").write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["output accepted"],
            "constraints": [], "required_outputs": ["output.txt"],
            "protected_paths": ["issue.md", "public_check.py"],
            "command": [sys.executable, "-B", "public_check.py"],
            "timeout_s": 10}), encoding="utf-8")
        self.worker = FakeWorker()
        self.executor = TaskExecutor(self.actor, self.worker)
        self.executor.admit(goal="Review the output", scope=["output.txt"],
                            permissions=["read", "edit"],
                            acceptance_path=self.actor / "acceptance.json",
                            input_paths=["issue.md", "public_check.py"],
                            budget_usd=1.0, authority_id="public-risk-grant",
                            actor="test", root_id="producer")
        self.state = self.executor.run("producer", stop_after_attempts=1)
        self.risk = {"schema_version": 1, "eligible": True,
                     "source": "issue.md",
                     "source_sha256": boundary.digest(
                         (self.actor / "issue.md").read_bytes()),
                     "quote": self.quote,
                     "finding": "The public check covers one nominal output path only.",
                     "next_check": "Check the other output path before accepting the repair."}
        self.risk_digest = controller_evaluation.digest(self.risk)

    def test_accepted_public_actor_clones_once_with_exact_risk(self):
        self.assertEqual("accepted", self.state["state"])
        self.assertEqual(1, len(self.worker.calls))
        pair = self.base / "pair"
        record = review.twins(self.actor, FILES, self.state, self.risk,
                              self.risk_digest, pair)
        self.assertEqual("worker-sonnet-low", record["next_worker_cell"])
        self.assertEqual(0.1, record["producer_cost_usd"])
        self.assertEqual(self.risk_digest, record["risk_digest"])
        for name in FILES:
            self.assertEqual((pair / "S" / name).read_bytes(),
                             (pair / "A" / name).read_bytes())
        context = review.write_review_goals(pair, self.risk, self.risk_digest,
                                             "- old output\n+ accepted output")
        self.assertEqual(record, context["source_snapshot"])
        self.assertEqual((pair / "S/REVIEW.md").read_bytes(),
                         (pair / "A/REVIEW.md").read_bytes())
        self.assertIn("other output path", (pair / "S/REVIEW.md").read_text())
        with self.assertRaisesRegex(review.ReviewStop, "single-use"):
            review.write_review_goals(pair, self.risk, self.risk_digest,
                                      "- old output\n+ accepted output")
        with self.assertRaisesRegex(review.ReviewStop, "already used"):
            review.twins(self.actor, FILES, self.state, self.risk,
                         self.risk_digest, pair)

    def test_open_charge_bad_receipt_public_failure_and_tamper_stop(self):
        for mutation in (
            lambda s: s.update(state="ready"),
            lambda s: s["budget"].update(unresolved=["open-call"]),
            lambda s: s["attempts"][0]["receipt"].update(writer_stopped=False),
            lambda s: s["attempts"][0]["receipt"].update(identity_valid=False),
            lambda s: s["attempts"][0]["verification"].update(status="fail"),
            lambda s: s["attempts"].append(copy.deepcopy(s["attempts"][0])),
        ):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.state)
                mutation(changed)
                with self.assertRaises(review.ReviewStop):
                    review.qualify(self.actor, FILES, changed, self.risk,
                                   self.risk_digest)
        with self.assertRaises(review.ReviewStop):
            review.qualify(self.actor, FILES, self.state, self.risk,
                           "0" * 64)
        wrong = dict(self.risk, quote="This quote is absent from the issue.")
        with self.assertRaises(review.ReviewStop):
            review.qualify(self.actor, FILES, self.state, wrong,
                           controller_evaluation.digest(wrong))
        no_decision = dict(self.risk, eligible=False)
        with self.assertRaises(review.ReviewStop):
            review.qualify(self.actor, FILES, self.state, no_decision,
                           controller_evaluation.digest(no_decision))
        (self.actor / "output.txt").write_text("wrong", encoding="utf-8")
        with self.assertRaisesRegex(review.ReviewStop, "public check"):
            review.qualify(self.actor, FILES, self.state, self.risk,
                           self.risk_digest)
        (self.actor / "output.txt").write_text("accepted", encoding="utf-8")
        (self.actor / "package/extra.py").write_text("VALUE = 2\n", encoding="utf-8")
        with self.assertRaisesRegex(review.ReviewStop, "inventory"):
            review.qualify(self.actor, FILES, self.state, self.risk,
                           self.risk_digest)

    def test_review_goal_rejects_tampered_twin(self):
        pair = self.base / "pair"
        review.twins(self.actor, FILES, self.state, self.risk,
                     self.risk_digest, pair)
        (pair / "A/package/service.py").write_text("VALUE = 9\n", encoding="utf-8")
        with self.assertRaisesRegex(review.ReviewStop, "twin source changed"):
            review.write_review_goals(pair, self.risk, self.risk_digest,
                                      "accepted edit")

    def test_review_goal_matches_controller_public_issue(self):
        pair = self.base / "pair"
        review.twins(self.actor, FILES, self.state, self.risk,
                     self.risk_digest, pair)
        review.write_review_goals(pair, self.risk, self.risk_digest,
                                  "- wrong output\n+ accepted output")
        actor = pair / "A"
        goal = (actor / "REVIEW.md").read_text(encoding="utf-8")
        executor = TaskExecutor(actor, FakeWorker())
        executor.admit(goal=goal, scope=["output.txt"],
                       permissions=["read", "edit"],
                       acceptance_path=actor / "acceptance.json",
                       input_paths=["REVIEW.md", "issue.md", "public_check.py"],
                       budget_usd=1.0, authority_id="review-grant",
                       actor="test", root_id="review")
        state = executor.status("review")
        packet = controller_public_assessment.collect(
            actor, issue="REVIEW.md",
            source_paths=["REVIEW.md", "issue.md", "public_check.py",
                          "package/service.py"],
            quote_requests=[{"source": "issue.md", "quote": self.quote}],
            input_revision=state["definition"]["input_revision"])
        issue = next(row["content"] for row in packet["sources"]
                     if row["path"] == packet["issue_path"])
        self.assertEqual(goal, issue)
        self.assertEqual(goal, state["definition"]["goal"])


if __name__ == "__main__":
    unittest.main()
