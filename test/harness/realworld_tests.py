#!/usr/bin/env python3
"""Offline regression cases for the real-world evaluation foundation."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RealWorldFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.harness = load(ROOT / "test" / "harness" / "realworld.py", "realworld_harness")
        cls.freeze = load(ROOT / "tools" / "evaluation_freeze.py", "evaluation_freeze")
        cls.isolation = load(ROOT / "tools" / "realworld_isolation.py", "realworld_isolation")

    def test_catalogue_and_adversarial_graders(self):
        report = self.harness.report()
        self.assertEqual(report["result"], "PASS", report)
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(set(report["ready_tasks"]), {
            *(f"D{number:02d}" for number in range(1, 13)),
            *(f"H{number:02d}" for number in range(1, 13)),
        })
        self.assertEqual(report["corpus_tasks_remaining"], [])
        self.assertEqual(len(report["development_tasks"]), 12)
        self.assertEqual(len(report["reserved_tasks"]), 12)
        self.assertEqual(
            report["reserved_authoring"]["arm_label_blinding"],
            "not-provable-same-session",
        )
        self.assertTrue(report["isolation"]["passed"], report["isolation"])
        for task in report["tasks"]:
            outcomes = {row["variant"]: row["accepted"] for row in task["variants"]}
            self.assertTrue(outcomes["reference"])
            self.assertTrue(outcomes["alternative"])
            self.assertFalse(outcomes["original"])
            self.assertTrue(all(not outcomes[name] for name in self.harness.WRONG))
            self.assertTrue(all(attack["rejected"] for attack in task["attacks"]))

    def test_freeze_is_content_addressed_and_launch_closed(self):
        first = self.freeze.candidate()
        second = self.freeze.candidate()
        self.assertEqual(first["candidate_sha256"], second["candidate_sha256"])
        self.assertFalse(first["paid_launch_ready"])
        self.assertEqual(first["pilot"]["planned_episodes"], 24)
        self.assertTrue(first["episode_runner"]["valid"])
        self.assertTrue(first["live_calibration"]["valid"])
        self.assertNotIn(
            "offline episode runner and replay evidence are missing or invalid",
            first["blockers"],
        )
        self.assertNotIn(
            "live Claude CLI calibration has not confirmed served model IDs and billing roll-up",
            first["blockers"],
        )
        self.assertEqual(first["live_calibration"]["root_models"], ["claude-sonnet-5"])
        self.assertEqual(first["live_calibration"]["worker_models"], ["claude-sonnet-5"])
        self.assertTrue(first["live_episode_execution"]["adapter_implemented"])
        self.assertTrue(first["live_episode_execution"]["adapter_qualified"])
        self.assertTrue(first["live_episode_execution"]["policy_executor_implemented"])
        self.assertTrue(first["live_episode_execution"]["restart_safe_integration_qualified"])
        self.assertTrue(first["live_episode_execution"]["controller_adapter_implemented"])
        self.assertTrue(first["live_episode_execution"]["controller_adapter_qualified"])
        self.assertTrue(first["live_episode_execution"]["pilot_preflight_qualified"])
        self.assertNotIn(
            "live policy executor and restart-safe episode integration are missing or invalid",
            first["blockers"],
        )
        self.assertNotIn(
            "live Controller escalation adapter and offline qualification evidence are missing or invalid",
            first["blockers"],
        )
        self.assertIn("claude-sonnet-5", first["models"]["required_actual_ids"])
        self.assertIn("test/oracles/realworld/D01/test_hidden.py", first["bound_files"])
        self.assertIn(
            "test/fixtures/realworld/development/D11/variants/alternative/importer/state.py",
            first["bound_files"],
        )
        self.assertIn(
            "test/fixtures/realworld/development/D07/variants/reference/worker/runner.js",
            first["bound_files"],
        )
        self.assertIn(
            "test/oracles/realworld/D08/test_hidden.py",
            first["bound_files"],
        )
        self.assertIn(
            "test/fixtures/realworld/development/D09/variants/alternative/orders/types.py",
            first["bound_files"],
        )
        self.assertIn(
            "test/fixtures/realworld/development/D10/repo/case_b/CONSTRAINT.md",
            first["bound_files"],
        )
        self.assertIn("tools/evaluation_runner.py", first["bound_files"])
        self.assertIn("test/results/2026-09-17-realworld-runner.json", first["bound_files"])
        self.assertIn("tools/evaluation_live_episode.py", first["bound_files"])
        self.assertIn("tools/evaluation_live_controller.py", first["bound_files"])
        self.assertIn("tools/evaluation_pilot.py", first["bound_files"])
        self.assertIn(
            "test/results/2026-09-18-live-controller-adapter.json",
            first["bound_files"],
        )
        self.assertIn(
            "test/results/2026-09-17-live-episode-integration.json",
            first["bound_files"],
        )
        self.assertIn("test/oracles/realworld/H12/test_hidden.py", first["bound_files"])
        self.assertEqual(first["corpus"]["task_count"], 24)
        self.assertTrue(first["corpus"]["qualified"])
        self.assertTrue(first["development"]["qualified"])
        self.assertEqual(first["development"]["known_spend_usd"], 1.376153606)
        self.assertEqual(first["development"]["decision"]["baseline_retained"], "B0")
        self.assertEqual(first["development"]["decision"]["adaptive_candidate"], "B1")
        self.assertNotIn(
            "W07 development comparison evidence is missing or invalid",
            first["blockers"],
        )
        self.assertIn("tools/evaluation_development_result.py", first["bound_files"])
        self.assertIn(
            "test/results/2026-09-18-realworld-development.json",
            first["bound_files"],
        )
        self.assertTrue(first["reserved"]["qualified"])
        self.assertEqual(first["reserved"]["known_spend_usd"], 1.053580005)
        self.assertEqual(first["reserved"]["decision"]["qualified_default"], "B0")
        self.assertFalse(first["reserved"]["promotion_gates"]["promotion_gate_passed"])
        self.assertNotIn(
            "paid W08 reserved comparison has not been authorised",
            first["blockers"],
        )
        self.assertNotIn(
            "W08 reserved comparison evidence is missing or invalid",
            first["blockers"],
        )
        self.assertTrue(first["qualified_default"]["qualified"])
        self.assertEqual(first["qualified_default"]["policy_id"], "B0")
        self.assertEqual(
            first["qualified_default"]["sequence"],
            ["worker-sonnet-low", "worker-sonnet-low", "worker-opus-high"],
        )
        self.assertFalse(first["qualified_default"]["controller_allowed"])
        self.assertFalse(first["qualified_default"]["adaptive_routing_enabled"])
        self.assertTrue(all(first["qualified_default"]["checks"].values()))
        self.assertNotIn(
            "W09 qualified-default source or bundle is missing or invalid",
            first["blockers"],
        )
        self.assertIn("tools/route.py", first["bound_files"])
        self.assertIn("src/routing_priors.json", first["bound_files"])
        self.assertIn("test/harness/qualified_default_tests.py", first["bound_files"])
        self.assertIn("tools/evaluation_reserved_result.py", first["bound_files"])

    def test_recorded_wsl_isolation_boundary(self):
        path = ROOT / "test" / "results" / "2026-09-17-realworld-isolation.json"
        ok, detail = self.isolation.validate(path)
        self.assertTrue(ok, detail)

    def test_cli_reports_json(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "test" / "harness" / "realworld.py"), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["result"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
