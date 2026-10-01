#!/usr/bin/env python3
"""Offline regression tests for the live evaluation worker adapter."""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    name = "evaluation_live_worker"
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "evaluation_live_worker.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class LiveWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = load_module()

    def request(self, root: Path):
        return self.subject.WorkerRequest(
            actor_root=root, issue="Repair the defect.", allowed_edits=("service.py",),
            requested_cell="worker-sonnet-low", allowance_usd=4.0,
            policy="Make one bounded repair.", timeout_s=10,
        )

    def test_command_is_exact_model_restricted_and_tool_minimal(self):
        with tempfile.TemporaryDirectory(prefix="live-worker-command-") as folder:
            request = self.request(Path(folder))
            cmd = self.subject.LiveWorkerAdapter.command(request)
        sonnet = self.subject.model_registry.resolve_cell("worker-sonnet-low")
        self.assertEqual(cmd[cmd.index("--model") + 1], sonnet["cli_model"])
        self.assertEqual(cmd[cmd.index("--effort") + 1], "low")
        self.assertEqual(cmd[cmd.index("--tools") + 1], "Read,Edit,Write,Glob,Grep")
        self.assertIn("--restricted", cmd)
        self.assertIn("--safe-mode", cmd)
        self.assertNotIn("Task", cmd[cmd.index("--tools") + 1])
        self.assertNotIn("Bash", cmd[cmd.index("--tools") + 1])

    def test_fable_command_uses_its_explicit_provider_identity(self):
        with tempfile.TemporaryDirectory(prefix="live-worker-fable-") as folder:
            request = dataclasses.replace(
                self.request(Path(folder)), requested_cell="worker-fable-max"
            )
            cmd = self.subject.LiveWorkerAdapter.command(request)
        fable = self.subject.model_registry.resolve_cell("worker-fable-max")
        self.assertEqual(cmd[cmd.index("--model") + 1], fable["cli_model"])
        self.assertEqual(cmd[cmd.index("--effort") + 1], "max")

    def test_haiku_command_uses_registry_default_without_effort_flag(self):
        with tempfile.TemporaryDirectory(prefix="live-worker-haiku-") as folder:
            request = dataclasses.replace(
                self.request(Path(folder)), requested_cell="worker-haiku-default"
            )
            cmd = self.subject.LiveWorkerAdapter.command(request)
        haiku = self.subject.model_registry.resolve_cell("worker-haiku-default")
        self.assertEqual(cmd[cmd.index("--model") + 1], haiku["cli_model"])
        self.assertNotIn("--effort", cmd)

    def test_stream_keeps_auxiliary_billing_separate(self):
        registry = self.subject.model_registry.load()
        sonnet = self.subject.model_registry.resolve_cell("worker-sonnet-low", registry)["cli_model"]
        historical_haiku = next(
            model_id for model_id, model_class in registry["historical_model_ids"].items()
            if model_class == "haiku"
        )
        rows = [
            {"type": "assistant", "parent_tool_use_id": None,
             "message": {"model": sonnet}},
            {"type": "result", "modelUsage": {
                sonnet: {}, historical_haiku: {}}},
        ]
        parsed = self.subject.parse_stream("\n".join(json.dumps(row) for row in rows))
        self.assertEqual(parsed["root_models"], [sonnet])
        self.assertEqual(parsed["auxiliary_billed_models"], [historical_haiku])

    def test_timeout_never_becomes_zero_cost(self):
        def timeout(cmd, cwd, env, limit):
            raise subprocess.TimeoutExpired(cmd, limit)
        with tempfile.TemporaryDirectory(prefix="live-worker-timeout-") as folder:
            outcome = self.subject.LiveWorkerAdapter(timeout).run(self.request(Path(folder)))
        self.assertEqual(outcome["status"], "interrupted")
        self.assertFalse(outcome["terminal"])
        self.assertIsNone(outcome["cost_usd"])
        self.assertIsNone(outcome["usage"]["cost_usd"])

    def test_qualification_passes_without_model_calls(self):
        with tempfile.TemporaryDirectory(prefix="live-worker-qualification-") as folder:
            value = self.subject.run_qualification(Path(folder))
        self.assertEqual(value["result"], "PASS", value)
        self.assertEqual(value["model_calls"], 0)
        self.assertTrue(all(value["checks"].values()))

    def test_validation_rejects_tampering(self):
        with tempfile.TemporaryDirectory(prefix="live-worker-evidence-", dir=ROOT / "test" / "results") as folder:
            folder = Path(folder)
            report = folder / "report.md"
            report.write_text("qualification\n", encoding="utf-8")
            value = {
                "result": "PASS", "offline_only": True, "model_calls": 0,
                "implementation_sha256": self.subject.file_sha256(
                    ROOT / "tools" / "evaluation_live_worker.py"),
                "calibration": {
                    "file_sha256": self.subject.file_sha256(self.subject.CALIBRATION),
                    "original_file_sha256": self.subject.file_sha256(
                        self.subject.ORIGINAL_CALIBRATION),
                },
                "checks": {str(index): True for index in range(7)},
                "report": {"path": report.relative_to(ROOT).as_posix(),
                           "sha256": self.subject.file_sha256(report)},
            }
            value["evidence_sha256"] = self.subject.digest(value)
            path = folder / "evidence.json"
            self.subject.atomic_json(path, value)
            self.assertTrue(self.subject.validate(path)[0])
            value["model_calls"] = 1
            self.subject.atomic_json(path, value)
            self.assertFalse(self.subject.validate(path)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
