#!/usr/bin/env python3
"""Provider-free checks of the real WSL public-verification boundary."""
from __future__ import annotations

import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import acceptance  # noqa: E402
import worker_wsl_attestation as host_attestation  # noqa: E402
from worker_wsl_transport import (TransportError, public_verify_isolated,
                                  wsl_public_command_runner)  # noqa: E402


class PublicVerifyTests(unittest.TestCase):
    def actor(self, directory: str, check: str) -> Path:
        root = Path(directory)
        (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "public_check.py").write_text(check, encoding="utf-8")
        (root / "ISSUE.md").write_text("Check the public behaviour.\n", encoding="utf-8")
        (root / "acceptance.json").write_text('{"version":1}\n', encoding="utf-8")
        return root

    def test_public_check_runs_in_wsl_without_changing_source(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "test" / "results") as directory:
            actor = self.actor(directory, "from app import VALUE\nassert VALUE == 1\n")
            result = public_verify_isolated(actor, 10)
            self.assertEqual(0, result["exit_code"])
            self.assertEqual("VALUE = 1\n", (actor / "app.py").read_text())

    def test_hidden_evaluator_is_unreadable(self) -> None:
        check = ("from pathlib import Path\n"
                 "try:\n"
                 "    Path('/var/lib/orchestrator-worker-n4/evaluator/oracle.py').read_text()\n"
                 "except OSError:\n"
                 "    pass\n"
                 "else:\n"
                 "    raise SystemExit(9)\n")
        with tempfile.TemporaryDirectory(dir=ROOT / "test" / "results") as directory:
            result = public_verify_isolated(self.actor(directory, check), 10)
            self.assertEqual(0, result["exit_code"])

    def test_self_modifying_public_check_is_rejected(self) -> None:
        check = "from pathlib import Path\nPath('app.py').write_text('VALUE = 2\\n')\n"
        with tempfile.TemporaryDirectory(dir=ROOT / "test" / "results") as directory:
            actor = self.actor(directory, check)
            with self.assertRaisesRegex(TransportError, "changed its fresh copy"):
                public_verify_isolated(actor, 10)
            self.assertEqual("VALUE = 1\n", (actor / "app.py").read_text())

    def test_acceptance_uses_attested_wsl_public_runner(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "test" / "results") as directory:
            actor = self.actor(directory, "from app import VALUE\nassert VALUE == 1\n")
            contract = {
                "version": 1, "kind": "command", "criteria": ["VALUE is 1"],
                "constraints": [], "required_outputs": ["app.py"],
                "protected_paths": ["public_check.py", "ISSUE.md", "acceptance.json"],
                "command": ["python3", "public_check.py"], "rubric": [],
                "timeout_s": 10,
            }
            contract_path = actor / "acceptance.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            frozen = acceptance.load_contract(actor, contract_path)
            # Host attestation is tested separately; its manifest legitimately
            # changes during a bundle build. This check exercises the real WSL
            # verifier and acceptance binding without freezing that manifest.
            with mock.patch.object(host_attestation, "validate", return_value=True):
                result = acceptance.verify(actor, frozen, "wsl-public-check",
                                           command_runner=wsl_public_command_runner)
            self.assertEqual("pass", result["status"])
            self.assertTrue(acceptance.qualified(result))
            proof = result["evidence"]["command"]["isolation_evidence"]
            self.assertEqual("fresh WSL mount+PID namespace, uid 65534, no credentials",
                             proof["boundary"])
            self.assertEqual("VALUE = 1\n", (actor / "app.py").read_text())


if __name__ == "__main__":
    unittest.main()
