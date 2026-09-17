#!/usr/bin/env python3
"""Offline Stage 4 acceptance, provenance and recovery regressions."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import acceptance  # noqa: E402
import route  # noqa: E402
import validate_records  # noqa: E402


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="acceptance-test-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / "tests").mkdir()
        (self.project / "tests" / "protected.py").write_text("assert True\n", encoding="utf-8")
        (self.project / "result.txt").write_text("initial\n", encoding="utf-8")
        self.contract_path = self.project / "acceptance.json"

    def contract(self, *, command=None, kind="command", rubric=None, outputs=None,
                 protected=None, timeout=10):
        value = {
            "version": 1, "kind": kind, "criteria": ["the result meets the task"],
            "constraints": ["do not weaken protected tests"],
            "required_outputs": outputs or ["result.txt"],
            "protected_paths": ["tests/protected.py"] if protected is None else protected,
            "command": command if command is not None else [sys.executable, "-c", "raise SystemExit(0)"],
            "rubric": rubric or [], "timeout_s": timeout,
        }
        if kind == "rubric":
            value["command"] = []
            value["rubric"] = rubric or ["review correctness and constraint compliance"]
        self.contract_path.write_text(json.dumps(value), encoding="utf-8")
        return acceptance.load_contract(self.project, self.contract_path)

    def test_claimed_pass_with_failing_check_is_acceptance_fail(self):
        frozen = self.contract(command=[sys.executable, "-c", "raise SystemExit(3)"])
        resolved = acceptance.verify(self.project, frozen, "led-001")
        self.assertEqual(resolved["status"], "fail")
        self.assertTrue(acceptance.qualified(resolved))
        self.assertEqual(resolved["evidence"]["command"]["exit_code"], 3)

    def test_missing_output_fails_and_missing_command_blocks(self):
        frozen = self.contract(outputs=["missing.txt"])
        self.assertEqual(acceptance.verify(self.project, frozen, "led-001")["status"], "fail")
        frozen = self.contract(command=["command-that-does-not-exist-stage4"])
        blocked = acceptance.verify(self.project, frozen, "led-002")
        self.assertEqual(blocked["status"], "blocked")
        self.assertFalse(acceptance.qualified(blocked))

    def test_timeout_is_blocked_and_cannot_train(self):
        frozen = self.contract(command=[sys.executable, "-c", "import time; time.sleep(2)"], timeout=.05)
        resolved = acceptance.verify(self.project, frozen, "led-001")
        self.assertEqual(resolved["status"], "blocked")
        self.assertTrue(resolved["evidence"]["command"]["timed_out"])
        self.assertFalse(acceptance.qualified(resolved))

    def test_changed_artifact_invalidates_cached_evidence_and_reruns(self):
        marker = self.project / "count.txt"
        script = ("from pathlib import Path; p=Path('count.txt'); "
                  "n=int(p.read_text())+1 if p.exists() else 1; p.write_text(str(n))")
        frozen = self.contract(command=[sys.executable, "-c", script])
        first = acceptance.verify(self.project, frozen, "led-001")
        self.assertEqual(first["status"], "pass")
        (self.project / "result.txt").write_text("edited after verification\n", encoding="utf-8")
        second = acceptance.verify(self.project, frozen, "led-001")
        self.assertEqual(marker.read_text(), "2")
        self.assertNotEqual(first["evidence"]["artefacts"]["digest"],
                            second["evidence"]["artefacts"]["digest"])

    def test_tampered_evidence_file_is_not_reused(self):
        marker = self.project / "count.txt"
        script = ("from pathlib import Path; p=Path('count.txt'); "
                  "n=int(p.read_text())+1 if p.exists() else 1; p.write_text(str(n))")
        frozen = self.contract(command=[sys.executable, "-c", script])
        acceptance.verify(self.project, frozen, "led-001")
        path = self.project / ".claude" / "acceptance" / "led-001.json"
        payload = json.loads(path.read_text())
        payload["acceptance"]["status"] = "fail"
        path.write_text(json.dumps(payload), encoding="utf-8")
        acceptance.verify(self.project, frozen, "led-001")
        self.assertEqual(marker.read_text(), "2")

    def test_protected_test_change_cannot_earn_pass(self):
        script = "from pathlib import Path; Path('tests/protected.py').write_text('assert False\\n')"
        frozen = self.contract(command=[sys.executable, "-c", script])
        resolved = acceptance.verify(self.project, frozen, "led-001")
        self.assertEqual(resolved["status"], "fail")
        self.assertFalse(resolved["evidence"]["protected_unchanged"])

    def test_rubric_requires_explicit_review_and_conflicts_fail_closed(self):
        frozen = self.contract(kind="rubric")
        staged = acceptance.verify(self.project, frozen, "led-001")
        self.assertEqual(staged["status"], "review_required")
        self.assertFalse(acceptance.qualified(staged))
        reviewed = acceptance.review(self.project, staged, "led-001", "pass", "operator", "checked")
        self.assertTrue(acceptance.qualified(reviewed))
        self.assertEqual(acceptance.review(self.project, reviewed, "led-001", "pass", "operator", "checked"), reviewed)
        with self.assertRaises(acceptance.AcceptanceError):
            acceptance.review(self.project, reviewed, "led-001", "fail", "operator", "changed")

    def test_unowned_boolean_cannot_train(self):
        self.assertFalse(acceptance.qualified({"status": "pass", "verified": True}))
        self.assertFalse(acceptance.qualified({"status": "pass", "contract_version": "acceptance-v2",
                                               "contract": {}, "contract_digest": "0" * 64}))
        frozen = self.contract()
        resolved = acceptance.verify(self.project, frozen, "led-001")
        resolved["status"] = "fail"
        self.assertFalse(acceptance.qualified(resolved))

    def test_crash_window_leaves_pending_entry_and_reusable_evidence(self):
        frozen = self.contract()
        ledger = route.default_ledger_path(self.project)
        pending = {"type": "RoutingLedgerEntry", "references": [], "ts": acceptance.utc_now(),
                   "task_slug": "crash", "bucket": "mechanical/short/contained", "self_directed": False,
                   "first_cell": "worker-sonnet-low", "escalations": [], "final_outcome": "unknown",
                   "cost_usd": None, "wall_clock_s": None, "controller_run_dir": None,
                   "winning_technique": None, "notes": "pending: crash", "context": {"source": "none"},
                   **route._entry_v2_fields("worker-sonnet-low", [], "unknown", None, None, [], pending=True),
                   "acceptance": frozen}
        pending = route.create_ledger_entry(ledger, pending)
        acceptance.verify(self.project, frozen, pending["id"])
        report = route.recover_report(self.project)
        self.assertIn("reusable evidence exists", report)
        self.assertIn("no hook/status output was observed", report)
        self.assertEqual(route.load_ledger(ledger)[0]["final_outcome"], "unknown")

    def test_route_completion_runs_owned_verifier_and_duplicate_is_idempotent(self):
        self.contract()
        line = "assessment: mechanical, short, contained; self_directed: false; prior_failure: none"
        common = ["--project", str(self.project), "--from-line", line]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = route.main(["--spawn", *common, "--task-slug", "owned",
                               "--first-cell", "worker-sonnet-low", "--worker-name", "owned",
                               "--acceptance-contract", str(self.contract_path)])
        self.assertEqual(code, 0)
        ident = out.getvalue().strip().splitlines()[-1]
        completion = ["--record", "--pending", ident, "--project", str(self.project),
                      "--outcome", "pass", "--cost-usd", "0", "--wall-clock-s", "1"]
        self.assertEqual(route.main(completion), 0)
        entry = route.load_ledger(route.default_ledger_path(self.project))[0]
        self.assertEqual(entry["acceptance"]["status"], "pass")
        self.assertEqual(validate_records.validate_record(entry, validate_records.load_schemas()), [])
        with mock.patch.object(acceptance, "verify", side_effect=AssertionError("must not rerun")):
            self.assertEqual(route.main(completion), 0)
            conflict = completion.copy()
            conflict[conflict.index("0")] = "0.5"
            self.assertEqual(route.main(conflict), 1)


if __name__ == "__main__":
    unittest.main()
