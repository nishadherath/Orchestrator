#!/usr/bin/env python3
"""Offline regression tests for live episode policy and recovery."""
from __future__ import annotations

import dataclasses
import importlib.util
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    name = "evaluation_live_episode"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / "evaluation_live_episode.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class LiveEpisodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = load_module()

    def test_policy_executor_has_no_hidden_or_task_inputs(self):
        signature = inspect.signature(self.subject.PolicyExecutor.decide)
        self.assertEqual(list(signature.parameters), ["self", "history"])
        constructor = inspect.signature(self.subject.PolicyExecutor)
        self.assertEqual(list(constructor.parameters), ["policy_id", "route_plan"])

    def test_b0_has_fixed_three_worker_ceiling_and_no_controller(self):
        policy = self.subject.PolicyExecutor("B0", {})
        history = []
        cells = []
        for index in range(3):
            action = policy.decide(history)
            cells.append(action["requested_cell"])
            history.append({
                "kind": "worker", "requested_cell": action["requested_cell"],
                "public_passed": False, "actor_digest": str(index),
            })
        self.assertEqual(cells, [
            "worker-sonnet-low", "worker-sonnet-low", "worker-opus-high",
        ])
        self.assertEqual(policy.decide(history)["kind"], "stop")
        self.assertNotIn("controller", cells)

    def test_b2_same_hypothesis_does_not_trigger_controller(self):
        policy = self.subject.PolicyExecutor("B2", {})
        history = [
            {"kind": "worker", "requested_cell": "worker-sonnet-low",
             "public_passed": False, "actor_digest": "same"},
            {"kind": "worker", "requested_cell": "worker-sonnet-low",
             "public_passed": False, "actor_digest": "same"},
        ]
        action = policy.decide(history)
        self.assertEqual(action, {
            "kind": "stop", "reason": "repeated_hypothesis_without_new_evidence",
        })

    def test_crash_recovery_retains_allowance_and_never_redispatches(self):
        with tempfile.TemporaryDirectory(prefix="live-episode-crash-") as folder:
            root = Path(folder)
            spec = self.subject.LiveEpisodeSpec("episode", "D01", "B0")
            first = self.subject.ScriptedWorker([
                RuntimeError("synthetic crash after dispatch")])
            with self.assertRaisesRegex(RuntimeError, "synthetic crash"):
                self.subject.LiveEpisodeRunner(root, first).run(spec)
            second = self.subject.ScriptedWorker(["reference"])
            result = self.subject.LiveEpisodeRunner(root, second).run(spec)
        self.assertEqual(second.calls, [])
        self.assertEqual(result["stage"], "blocked")
        self.assertEqual(result["dispatch_events"], 1)
        self.assertGreater(result["reserved_usd"], 0)

    def test_crash_after_budget_start_before_dispatch_event_never_redispatches(self):
        with tempfile.TemporaryDirectory(prefix="live-episode-start-crash-") as folder:
            root = Path(folder)
            spec = self.subject.LiveEpisodeSpec("episode", "D01", "B0")
            first = self.subject.ScriptedWorker(["reference"])
            runner = self.subject.LiveEpisodeRunner(root, first)
            original_save = runner._save

            def fail_before_dispatch_event(paths, state, stage, event, details):
                if event == "action_dispatched":
                    raise RuntimeError("synthetic crash after budget start")
                original_save(paths, state, stage, event, details)

            runner._save = fail_before_dispatch_event
            with self.assertRaisesRegex(RuntimeError, "after budget start"):
                runner.run(spec)
            second = self.subject.ScriptedWorker(["reference"])
            result = self.subject.LiveEpisodeRunner(root, second).run(spec)
        self.assertEqual(first.calls, [])
        self.assertEqual(second.calls, [])
        self.assertEqual(result["stage"], "blocked")
        self.assertEqual(result["dispatch_events"], 0)
        self.assertGreater(result["reserved_usd"], 0)

    def test_controller_absence_blocks_before_dispatch(self):
        route_plan = {"first": "controller", "execution_ladder": []}
        with tempfile.TemporaryDirectory(prefix="live-episode-controller-") as folder:
            worker = self.subject.ScriptedWorker(["reference"])
            runner = self.subject.LiveEpisodeRunner(Path(folder), worker)
            spec = self.subject.LiveEpisodeSpec("episode", "D01", "B1")
            original = self.subject.load_frozen_plan
            try:
                self.subject.load_frozen_plan = lambda ignored: route_plan
                result = runner.run(spec)
            finally:
                self.subject.load_frozen_plan = original
        self.assertEqual(result["stage"], "blocked")
        self.assertEqual(result["stop_reason"], "live_controller_adapter_missing")
        self.assertEqual(result["dispatch_events"], 0)
        self.assertEqual(worker.calls, [])

    def test_missing_cost_blocks_before_hidden_grade(self):
        with tempfile.TemporaryDirectory(prefix="live-episode-cost-") as folder:
            worker = self.subject.ScriptedWorker(["reference"], cost_usd=None)
            runner = self.subject.LiveEpisodeRunner(Path(folder), worker)
            result = runner.run(self.subject.LiveEpisodeSpec("episode", "D01", "B0"))
        self.assertEqual(result["stage"], "blocked")
        self.assertIsNone(result["grade"])
        self.assertGreater(result["reserved_usd"], 0)

    def test_qualification_passes_without_model_calls(self):
        with tempfile.TemporaryDirectory(prefix="live-episode-qualification-") as folder:
            value = self.subject.run_qualification(Path(folder))
        self.assertEqual(value["result"], "PASS", value)
        self.assertEqual(value["model_calls"], 0)
        self.assertTrue(all(value["checks"].values()))

    def test_validation_rejects_tampering(self):
        source = json.loads(self.subject.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="live-episode-evidence-",
                                         dir=ROOT / "test" / "results") as folder:
            path = Path(folder) / "evidence.json"
            self.subject.atomic_json(path, source)
            self.assertTrue(self.subject.validate(path)[0])
            source["model_calls"] = 1
            self.subject.atomic_json(path, source)
            self.assertFalse(self.subject.validate(path)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
