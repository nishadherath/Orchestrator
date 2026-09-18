#!/usr/bin/env python3
"""Offline qualification of the complete model/effort registry."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import evaluation_live_worker as live_worker  # noqa: E402
import evaluation_runner  # noqa: E402
import model_registry  # noqa: E402
import system_controller  # noqa: E402


def load_preflight():
    spec = importlib.util.spec_from_file_location("registry_preflight", ROOT / "src" / "preflight.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ModelRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = model_registry.load()
        cls.preflight = load_preflight()

    def test_registry_is_exact_complete_matrix(self):
        self.assertEqual(len(self.registry["cells"]), 15)
        self.assertEqual(model_registry.models(self.registry), ("sonnet", "opus", "fable"))
        self.assertEqual(model_registry.efforts(self.registry),
                         ("low", "medium", "high", "xhigh", "max"))
        self.assertNotIn("haiku", self.registry["models"])

    def test_all_fifteen_cells_build_exact_fake_dispatch_commands(self):
        with tempfile.TemporaryDirectory(prefix="registry-commands-") as folder:
            root = Path(folder)
            for name in self.registry["cells"]:
                resolved = model_registry.resolve_cell(name, self.registry)
                self.assertEqual(resolved["qualification"]["status"], "offline-wiring")
                self.assertEqual(resolved["qualification"]["live_quality"], "unqualified")
                request = live_worker.WorkerRequest(
                    actor_root=root, issue="Inspect wiring.", allowed_edits=("file.py",),
                    requested_cell=name, allowance_usd=1.0, policy="No provider call.",
                )
                command = live_worker.LiveWorkerAdapter.command(request)
                self.assertEqual(command[command.index("--model") + 1], resolved["cli_model"])
                self.assertEqual(command[command.index("--effort") + 1], resolved["effort"])

    def test_fable_identity_is_explicit_and_silent_substitution_fails(self):
        name = "worker-fable-xhigh"
        resolved = model_registry.resolve_cell(name, self.registry)
        self.assertEqual(resolved["expected_provider_model"], "claude-fable-5-1")
        self.assertFalse(model_registry.identity_matches(name, "claude-sonnet-5", registry=self.registry))
        self.assertTrue(model_registry.identity_matches(name, "claude-fable-5-1", registry=self.registry))
        self.assertFalse(model_registry.identity_matches(
            name, "claude-fable-5-1", ["claude-sonnet-5"], self.registry
        ))

        usage = {field: 1 for field in live_worker.USAGE_FIELDS}
        call = {"cost_usd": 0.1, "usage": usage,
                "model_usage": {"claude-sonnet-5": {"costUSD": 0.1}}}
        with tempfile.TemporaryDirectory(prefix="registry-substitution-") as folder:
            root = Path(folder)
            request = live_worker.WorkerRequest(
                actor_root=root, issue="Inspect wiring.", allowed_edits=("file.py",),
                requested_cell=name, allowance_usd=1.0, policy="No edits.",
            )
            adapter = live_worker.LiveWorkerAdapter(
                lambda cmd, cwd, env, timeout: subprocess.CompletedProcess(
                    cmd, 0, live_worker._stream("claude-sonnet-5", call), ""
                )
            )
            outcome = adapter.run(request)
        self.assertFalse(outcome["identity_valid"])
        self.assertEqual(outcome["status"], "failed")
        self.assertEqual(outcome["expected_model"], "claude-fable-5-1")

    def test_evaluator_uses_registry_for_every_cell(self):
        for name in self.registry["cells"]:
            self.assertEqual(
                evaluation_runner.expected_model(name),
                model_registry.resolve_cell(name, self.registry)["expected_provider_model"],
            )

    def test_role_profiles_are_valid_and_standard_drives_controller(self):
        standard = model_registry.resolve_role_profile("standard", self.registry)
        expected = {
            role: (cells[0]["model"], cells[0]["effort"])
            for role, cells in standard["roles"].items()
        }
        self.assertEqual(system_controller.QUICK_CELLS, expected)
        frontier = model_registry.resolve_role_profile("frontier-candidate", self.registry)
        used_models = {cell["model"] for cells in frontier["roles"].values() for cell in cells}
        used_efforts = {cell["effort"] for cells in frontier["roles"].values() for cell in cells}
        self.assertEqual(used_models, {"sonnet", "opus", "fable"})
        self.assertEqual(used_efforts, {"low", "medium", "high", "xhigh", "max"})
        self.assertEqual(frontier["status"], "unqualified-experimental")

    def test_unknown_prices_remain_unknown(self):
        known = model_registry.projected_cost("worker-sonnet-low", registry=self.registry)
        unknown = model_registry.projected_cost("worker-fable-low", registry=self.registry)
        self.assertTrue(known["known"])
        self.assertGreater(known["cost_per_run_usd"], 0)
        self.assertFalse(unknown["known"])
        self.assertIsNone(unknown["cost_per_run_usd"])
        self.assertIsNone(unknown["wall_clock_s"])

    def test_preflight_uses_exact_identity_and_effort(self):
        entry = {"id": "led-001", "first_cell": "worker-fable-low"}
        correct = self.preflight._model_effort_observation(entry, {
            "id": "att-001", "actual_model": "claude-fable-5-1",
            "effort_evidence": "cli-argument:low",
        })
        substituted = self.preflight._model_effort_observation(entry, {
            "id": "att-002", "actual_model": "claude-sonnet-5",
            "effort_evidence": "cli-argument:xhigh",
        })
        self.assertTrue(correct["model_match"] and correct["effort_match"])
        self.assertFalse(substituted["model_match"] or substituted["effort_match"])

    def test_unsupported_cells_and_profiles_fail_visibly(self):
        with self.assertRaisesRegex(model_registry.RegistryError, "unsupported worker cell"):
            model_registry.resolve_cell("worker-haiku-low", self.registry)
        with self.assertRaisesRegex(model_registry.RegistryError, "unsupported Controller role profile"):
            model_registry.resolve_role_profile("invented", self.registry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
