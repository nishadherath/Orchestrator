#!/usr/bin/env python3
"""Provider-free WSL public-interpreter identity, command and cost checks."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test.harness.controller_x3_pair_tests import interpret_public, prepare
from test.harness.controller_x4_assessment_tests import AssessmentTests

import controller_wsl_interpreter
import controller_wsl_launch
import controller_workflow
import task_executor
from test.harness.controller_routing_r4_tests import FakeAdapter as FakeController


CLAUDE = "/opt/orchestrator-worker-runtime/bin/claude"


class ScriptedWsl:
    def __init__(self, model: str, mode: str = "success"):
        self.model = model
        self.mode = mode
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if command[-3:] == ["auth", "status", "--json"]:
            if self.mode == "empty-auth":
                return subprocess.CompletedProcess(command, 0, None, "")
            state = {"loggedIn": self.mode != "no-auth", "authMethod": "claude.ai",
                     "subscriptionType": "max"}
            return subprocess.CompletedProcess(command, 0, json.dumps(state), "")
        if command[-3:-1] == ["/usr/bin/test", "-r"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if self.mode == "cli-parser-error":
            return subprocess.CompletedProcess(
                command, 1, "", "Error: --json-schema is not valid JSON: parse error\n")
        packet = json.loads(kwargs["input"])
        interpretation = interpret_public(packet)["interpretation"]
        model = "unrelated-served-model" if self.mode == "wrong-model" else self.model
        final = {"type": "result", "subtype": "success",
                 "total_cost_usd": .04, "usage": {"input_tokens": 100,
                                                  "output_tokens": 20},
                 "result": json.dumps(interpretation)}
        if self.mode == "bad-output":
            final["result"] = "not JSON"
        stream = "\n".join(json.dumps(row) for row in (
            {"type": "assistant", "parent_tool_use_id": None,
             "message": {"model": model}}, final)) + "\n"
        if self.mode == "timeout":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"],
                                            output=stream.encode())
        return subprocess.CompletedProcess(command, 0, stream, "")


class InterpreterTests(unittest.TestCase):
    def setup_root(self, raw: str):
        executor, root, worker = prepare(Path(raw) / "actor", "C03-D1")
        options = AssessmentTests().inputs(executor, root)
        model = controller_wsl_interpreter.model_registry.resolve_role_profile(
            "standard")["roles"]["controller"][0]["expected_provider_model"]
        return executor, root, worker, options, model

    @staticmethod
    def interpreter(script: ScriptedWsl, allowance: float = .5):
        return controller_wsl_interpreter.WslPublicInterpreter(
            distro="kali-linux", linux_user="wsl", claude_path=CLAUDE,
            allowance_usd=allowance, runner=script)

    def test_success_uses_tool_free_wsl_and_settles_root(self):
        with tempfile.TemporaryDirectory(prefix="x4-wsl-success-") as raw:
            executor, root, worker, options, model = self.setup_root(raw)
            script = ScriptedWsl(model)
            with mock.patch.dict(os.environ, {
                    "ANTHROPIC_API_KEY": "not-for-wsl", "CLAUDE_CODE_EFFORT_LEVEL": "max",
                    "WSLENV": "ANTHROPIC_API_KEY/u"}):
                result = executor.assess_public(
                    root, interpreter=self.interpreter(script), **options)
            self.assertEqual(3, len(script.calls))
            command, kwargs = script.calls[2]
            self.assertEqual(["wsl.exe", "-d", "kali-linux", "-u", "wsl"],
                             command[:5])
            self.assertEqual("/usr/bin/python3", command[9])
            self.assertTrue(command[10].endswith("controller_wsl_launch.py"))
            linux_command = controller_wsl_launch.command(command[11:])
            self.assertIn("--restricted", linux_command)
            self.assertIn("--safe-mode", linux_command)
            self.assertIn("--strict-mcp-config", linux_command)
            self.assertEqual("", linux_command[linux_command.index("--tools") + 1])
            self.assertEqual("object", json.loads(
                linux_command[linux_command.index("--json-schema") + 1])["type"])
            self.assertNotIn("not-for-wsl", kwargs["input"])
            self.assertNotIn("ANTHROPIC_API_KEY", kwargs["env"])
            self.assertNotIn("WSLENV", kwargs["env"])
            self.assertEqual("settled", executor.status(root)["public_assessment"]["status"])
            self.assertEqual(.04, executor.status(root)["budget"]["spent_usd"])
            self.assertEqual(model, result["telemetry"]["model"])
            self.assertEqual([], worker.calls)

    def test_failed_auth_or_cap_mismatch_never_reserves_or_calls_model(self):
        with tempfile.TemporaryDirectory(prefix="x4-wsl-preflight-") as raw:
            executor, root, _, options, model = self.setup_root(raw)
            script = ScriptedWsl(model, "no-auth")
            with self.assertRaisesRegex(task_executor.ExecutorError, "preflight failed"):
                executor.assess_public(root, interpreter=self.interpreter(script),
                                       **options)
            self.assertEqual(1, len(script.calls))
            self.assertIsNone(executor.status(root).get("public_assessment"))
            self.assertEqual(0, executor.status(root)["budget"]["spent_usd"])
            with self.assertRaisesRegex(task_executor.ExecutorError,
                                        "cap differs"):
                executor.assess_public(root, interpreter=self.interpreter(script, .6),
                                       **options)
            self.assertEqual(1, len(script.calls))

    def test_empty_auth_response_never_reserves_or_calls_model(self):
        with tempfile.TemporaryDirectory(prefix="x4-wsl-empty-auth-") as raw:
            executor, root, _, options, model = self.setup_root(raw)
            script = ScriptedWsl(model, "empty-auth")
            with self.assertRaisesRegex(task_executor.ExecutorError, "preflight failed"):
                executor.assess_public(root, interpreter=self.interpreter(script),
                                       **options)
            self.assertEqual(1, len(script.calls))
            self.assertIsNone(executor.status(root).get("public_assessment"))
            self.assertEqual(0, executor.status(root)["budget"]["spent_usd"])

    def test_terminal_invalid_output_and_identity_retain_charges(self):
        for mode in ("bad-output", "wrong-model"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(
                    prefix="x4-wsl-invalid-") as raw:
                executor, root, worker, options, model = self.setup_root(raw)
                with self.assertRaises(task_executor.ExecutorError):
                    executor.assess_public(
                        root, interpreter=self.interpreter(ScriptedWsl(model, mode)),
                        **options)
                record = executor.status(root)
                self.assertEqual("invalid", record["public_assessment"]["status"])
                self.assertEqual(.04, record["budget"]["spent_usd"])
                self.assertEqual([], record["budget"]["unresolved"])
                self.assertEqual([], worker.calls)

    def test_local_cli_parser_rejection_settles_zero_without_replay(self):
        with tempfile.TemporaryDirectory(prefix="x4-wsl-cli-error-") as raw:
            executor, root, worker, options, model = self.setup_root(raw)
            script = ScriptedWsl(model, "cli-parser-error")
            with self.assertRaises(task_executor.ExecutorError):
                executor.assess_public(root, interpreter=self.interpreter(script),
                                       **options)
            record = executor.status(root)
            self.assertEqual("invalid", record["public_assessment"]["status"])
            self.assertEqual("blocked", record["state"])
            self.assertEqual(0, record["budget"]["spent_usd"])
            self.assertEqual([], record["budget"]["unresolved"])
            self.assertEqual([], worker.calls)

    def test_timeout_with_partial_charge_remains_unresolved(self):
        with tempfile.TemporaryDirectory(prefix="x4-wsl-timeout-") as raw:
            executor, root, _, options, model = self.setup_root(raw)
            with self.assertRaises(task_executor.ExecutorError):
                executor.assess_public(
                    root, interpreter=self.interpreter(ScriptedWsl(model, "timeout")),
                    **options)
            record = executor.status(root)
            self.assertEqual("uncertain", record["public_assessment"]["status"])
            self.assertEqual(.04, record["budget"]["spent_usd"])
            self.assertEqual([record["public_assessment"]["invocation_id"]],
                             record["budget"]["unresolved"])

    def test_same_interpreter_flows_through_routing_controller_and_worker(self):
        with tempfile.TemporaryDirectory(prefix="x4-wsl-workflow-") as raw:
            executor, root, worker, options, model = self.setup_root(raw)
            script = ScriptedWsl(model)
            controller = FakeController()
            result = controller_workflow.execute(
                executor, root, issue=options["issue"],
                source_paths=options["source_paths"],
                quote_requests=options["quote_requests"],
                operational=options["operational"],
                assessment_allowance_usd=options["maximum_usd"],
                interpreter=self.interpreter(script),
                controller_adapter=controller)
            self.assertEqual("accepted", result["task"]["state"])
            self.assertEqual("controller", result["decision"]["effective_action"])
            self.assertEqual(3, len(script.calls))
            self.assertEqual(1, controller.calls)
            self.assertEqual(1, len(worker.calls))
            self.assertEqual(.34, result["task"]["budget"]["spent_usd"])


if __name__ == "__main__":
    unittest.main()
