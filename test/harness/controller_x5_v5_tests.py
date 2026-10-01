#!/usr/bin/env python3
"""Provider-free checks for the revised X5 public evidence packet."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_public_assessment as public  # noqa: E402
import controller_x5_v5_screen as screen  # noqa: E402


class X5V5PacketTests(unittest.TestCase):
    def test_every_issue_line_is_citable_and_packet_validates(self) -> None:
        roots = {task: ROOT / "test/fixtures/controller_x5_v4" / directory / "actor"
                 for task, directory in screen.CASE_DIRS.items()}
        roots.update({task: ROOT / "test/fixtures/controller_x3/development" /
                      task / "actor" for task in ("N01-D1", "C08-D2")})
        for task, actor in roots.items():
            with self.subTest(task=task):
                editable = json.loads((actor / "acceptance.json").read_text(
                    encoding="utf-8"))["editable_paths"]
                inputs = screen._inputs(actor, editable)
                packet = public.collect(
                    actor, issue=inputs["issue"],
                    source_paths=inputs["source_paths"],
                    quote_requests=inputs["quote_requests"],
                    input_revision={"task": task})
                issue_lines = [line for line in (actor / "issue.md").read_text(
                    encoding="utf-8").splitlines() if line.strip()]
                cited = {row["quote"] for row in packet["citations"]
                         if row["source"] == "issue.md"}
                self.assertEqual(set(issue_lines), cited)
                self.assertGreater(len(cited), 1)
                self.assertLessEqual(len(packet["citations"]), public.MAX_CITATIONS)
                self.assertFalse(any("oracle" in path or "variant" in path
                                     for path in inputs["source_paths"]))
                if task in screen.CASE_DIRS:
                    self.assertIn("trace.json", inputs["source_paths"])
                    self.assertTrue(any(row["source"] == "trace.json"
                                        for row in packet["citations"]))

    def test_first_miss_still_blocks_later_assessments(self) -> None:
        miss = {"task_id": "X5-PAY", "assessment_status": "settled",
                "decision_frozen": True, "effective_action": "worker",
                "budget_unresolved": []}
        with self.assertRaisesRegex(screen.ScreenError, "stopped after X5-PAY"):
            screen.gate_results("X5-FEAT", [miss])

    def test_gate_requires_a_durable_routing_decision(self) -> None:
        row = {"task_id": "X5-PAY", "assessment_status": "settled",
               "effective_action": "controller", "budget_unresolved": []}
        with self.assertRaisesRegex(screen.ScreenError, "stopped after X5-PAY"):
            screen.gate_results("X5-FEAT", [row])
        row["decision_frozen"] = True
        screen.gate_results("X5-FEAT", [row])


if __name__ == "__main__":
    unittest.main()
