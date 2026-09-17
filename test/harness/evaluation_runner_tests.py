#!/usr/bin/env python3
"""Offline regression cases for checkpointed real-world episodes."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "evaluation_runner", ROOT / "tools" / "evaluation_runner.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvaluationRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()

    def test_interruption_resumes_without_redispatch(self):
        episode = next(item for item in self.runner.SCENARIOS
                       if item.scenario == "interruption_resume")
        with tempfile.TemporaryDirectory(prefix="episode-resume-") as folder:
            runner = self.runner.EpisodeRunner(Path(folder))
            interrupted = runner.run(episode)
            self.assertEqual(interrupted["stage"], "worker_committed")
            self.assertEqual(interrupted["dispatch_events"], 1)
            resumed = runner.run(episode)
            self.assertEqual(resumed["stage"], "complete")
            self.assertEqual(resumed["dispatch_events"], 1)
            self.assertTrue(resumed["grade"]["accepted"])
            self.assertTrue(resumed["learning_eligible"])

    def test_transition_journal_recovers_after_append_failure(self):
        episode = self.runner.SCENARIOS[0]
        with tempfile.TemporaryDirectory(prefix="episode-transition-") as folder:
            runner = self.runner.EpisodeRunner(Path(folder))
            original = self.runner.append_event
            calls = 0

            def fail_second_append(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("synthetic journal interruption")
                return original(*args, **kwargs)

            self.runner.append_event = fail_second_append
            try:
                with self.assertRaisesRegex(OSError, "synthetic journal interruption"):
                    runner.run(episode)
            finally:
                self.runner.append_event = original
            resumed = runner.run(episode)
            self.assertEqual(resumed["stage"], "complete")
            self.assertEqual(resumed["dispatch_events"], 1)
            self.assertTrue(resumed["event_chain_valid"])

    def test_qualification_covers_failure_and_accounting_paths(self):
        with tempfile.TemporaryDirectory(prefix="episode-qualification-") as folder:
            evidence = self.runner.run_qualification(Path(folder))
        self.assertEqual(evidence["result"], "PASS", evidence)
        self.assertEqual(evidence["model_calls"], 0)
        self.assertEqual(evidence["policies"], ["B0", "B1", "B2"])
        self.assertEqual(evidence["scenario_count"], 9)
        self.assertEqual(evidence["accounting"]["known_spend_usd"], 1.4)
        self.assertEqual(evidence["accounting"]["retained_unresolved_usd"], 8.0)
        self.assertEqual(evidence["accounting"]["unknown_cost_episodes"], 2)
        rows = {row["scenario"]: row for row in evidence["scenarios"]}
        self.assertFalse(rows["identity_mismatch"]["learning_eligible"])
        self.assertFalse(rows["missing_usage"]["learning_eligible"])
        self.assertFalse(rows["cancellation"]["learning_eligible"])
        self.assertEqual(rows["grader_failure"]["grade"]["status"], "blocked")
        self.assertTrue(evidence["replay"]["deterministic"])

    def test_evidence_digest_rejects_tampering(self):
        with tempfile.TemporaryDirectory(prefix="episode-evidence-", dir=ROOT / "test" / "results") as folder:
            path = Path(folder) / "evidence.json"
            report = Path(folder) / "report.md"
            report.write_text("offline qualification\n", encoding="utf-8")
            value = {"schema_version": 1, "mode": self.runner.QUALIFICATION_MODE,
                     "model_calls": 0, "implementation_sha256": self.runner.file_sha256(
                         ROOT / "tools" / "evaluation_runner.py"),
                     "policies": ["B0", "B1", "B2"],
                     "scenario_count": len(self.runner.SCENARIOS),
                     "replay": {"deterministic": True, "event_chains_valid": True,
                                "one_dispatch_per_episode": True},
                     "report": {"path": report.relative_to(ROOT).as_posix(),
                                "sha256": self.runner.file_sha256(report)},
                     "result": "PASS"}
            value["evidence_sha256"] = self.runner.digest(value)
            self.runner.atomic_json(path, value)
            self.assertTrue(self.runner.validate_evidence(path)[0])
            changed = json.loads(path.read_text(encoding="utf-8"))
            changed["model_calls"] = 1
            self.runner.atomic_json(path, changed)
            self.assertFalse(self.runner.validate_evidence(path)[0])

    def test_event_chain_rejects_tampering(self):
        episode = self.runner.SCENARIOS[0]
        with tempfile.TemporaryDirectory(prefix="episode-events-") as folder:
            campaign = Path(folder)
            runner = self.runner.EpisodeRunner(campaign)
            runner.run(episode)
            events = runner._paths(episode)["events"]
            rows = events.read_text(encoding="utf-8").splitlines()
            changed = json.loads(rows[2])
            changed["details"]["requested_cell"] = "worker-opus-high"
            rows[2] = json.dumps(changed, sort_keys=True)
            events.write_text("\n".join(rows) + "\n", encoding="utf-8")
            ok, _ = self.runner.validate_events(events)
            self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
