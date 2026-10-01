"""Fake-provider proof of the settled first-failure comparison boundary."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_first_failure as checkpoint  # noqa: E402
from task_executor import TaskExecutor  # noqa: E402


FILES = {"acceptance.json", "issue.md", "public_check.py", "report.json",
         "output.txt", "package/service.py"}


class FakeWorker:
    def __init__(self, output: str):
        self.output = output
        self.calls = []

    def capability(self, root):
        return {"configured": True, "actor_root": str(root.resolve()),
                "enforcement_proven": False}

    def run(self, request):
        self.calls.append(request)
        (request.actor_root / "output.txt").write_text(self.output, encoding="utf-8")
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


class FirstFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="x5-first-failure-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.actor = self.base / "producer"
        self.actor.mkdir()
        (self.actor / "issue.md").write_text("Repair the output.\n", encoding="utf-8")
        (self.actor / "public_check.py").write_text(
            "from pathlib import Path\nassert Path('output.txt').read_text() == 'accepted'\n",
            encoding="utf-8")
        (self.actor / "report.json").write_text("{}\n", encoding="utf-8")
        (self.actor / "output.txt").write_text("wrong", encoding="utf-8")
        (self.actor / "package").mkdir()
        (self.actor / "package/service.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.actor / "acceptance.json").write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["output accepted"],
            "constraints": [], "required_outputs": ["output.txt"],
            "protected_paths": ["issue.md", "public_check.py"],
            "command": [sys.executable, "-B", "public_check.py"],
            "timeout_s": 10}), encoding="utf-8")

    def admit(self, actor: Path, worker: FakeWorker, root: str) -> TaskExecutor:
        entry = TaskExecutor(actor, worker)
        entry.admit(goal="Repair the output", scope=["output.txt"],
                    permissions=["read", "edit"],
                    acceptance_path=actor / "acceptance.json",
                    input_paths=["issue.md", "public_check.py"],
                    budget_usd=1.0, authority_id="grant-" + root,
                    actor="test", root_id=root)
        return entry

    def test_first_failure_twins_and_one_matched_worker_call(self):
        producer_worker = FakeWorker("wrong")
        producer = self.admit(self.actor, producer_worker, "producer")
        state = producer.run("producer", stop_after_attempts=1)
        self.assertEqual("ready", state["state"])
        self.assertEqual(1, len(producer_worker.calls))
        pair = self.base / "pair"
        record = checkpoint.twins(self.actor, FILES, state, pair)
        self.assertEqual("worker-sonnet-low", record["next_worker_cell"])
        self.assertEqual(1, record["successor_worker_attempts"])
        self.assertEqual(0.1, record["producer_cost_usd"])
        for name in FILES:
            self.assertEqual((pair / "S" / name).read_bytes(),
                             (pair / "A" / name).read_bytes())
        for arm in ("S", "A"):
            worker = FakeWorker("accepted")
            entry = self.admit(pair / arm, worker, arm.lower())
            result = entry.run(arm.lower(), stop_after_attempts=1)
            self.assertEqual("accepted", result["state"])
            self.assertEqual(1, len(worker.calls))
            self.assertEqual(record["next_worker_cell"], worker.calls[0].requested_cell)
            self.assertEqual(0.1, result["budget"]["spent_usd"])
        with self.assertRaisesRegex(checkpoint.CheckpointStop, "already used"):
            checkpoint.twins(self.actor, FILES, state, pair)

    def test_public_success_and_unsettled_attempt_never_clone(self):
        worker = FakeWorker("wrong")
        entry = self.admit(self.actor, worker, "negative")
        state = entry.run("negative", stop_after_attempts=1)
        for mutation in (
            lambda s: s.update(state="accepted"),
            lambda s: s["budget"].update(unresolved=["open-call"]),
            lambda s: s["attempts"][0]["receipt"].update(writer_stopped=False),
            lambda s: s["attempts"][0].update(process_state="uncertain"),
            lambda s: s["attempts"][0]["verification"].update(status="pass"),
            lambda s: s["attempts"].append(copy.deepcopy(s["attempts"][0])),
        ):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(state)
                mutation(changed)
                with self.assertRaises(checkpoint.CheckpointStop):
                    checkpoint.qualify(self.actor, FILES, changed)
        (self.actor / "output.txt").write_text("accepted", encoding="utf-8")
        with self.assertRaisesRegex(checkpoint.CheckpointStop, "public check"):
            checkpoint.qualify(self.actor, FILES, state)

    def test_nested_inventory_rejects_unlisted_and_redirected_source(self):
        unexpected = self.actor / "package/extra.py"
        unexpected.write_text("VALUE = 2\n", encoding="utf-8")
        with self.assertRaisesRegex(checkpoint.CheckpointStop, "inventory"):
            checkpoint.actor_files(self.actor, FILES)
        unexpected.unlink()
        source = self.actor / "package/service.py"
        source.unlink()
        source.symlink_to(self.actor / "issue.md")
        with self.assertRaisesRegex(checkpoint.CheckpointStop, "redirected"):
            checkpoint.actor_files(self.actor, FILES)


if __name__ == "__main__":
    unittest.main()
