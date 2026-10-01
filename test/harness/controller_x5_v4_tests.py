#!/usr/bin/env python3
"""Focused provider-free X5 v4 screen and scoring checks."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_v4_grade as grade
import controller_x5_v4_screen as screen


class X5V4Tests(unittest.TestCase):
    def test_sequential_gate_accepts_only_predeclared_actions(self):
        prior = []
        for task in screen.TASKS:
            screen.gate_results(task, prior)
            prior.append({"task_id": task, "assessment_status": "settled",
                          "effective_action": screen.EXPECTED_ACTIONS[task],
                          "budget_unresolved": []})

    def test_first_miss_stops_every_later_task(self):
        prior = [{"task_id": "X5-PAY", "assessment_status": "settled",
                  "effective_action": "worker", "budget_unresolved": []}]
        with self.assertRaisesRegex(screen.ScreenError, "stopped after X5-PAY"):
            screen.gate_results("X5-FEAT", prior)

    def test_unsettled_or_unresolved_result_blocks(self):
        row = {"task_id": "X5-PAY", "assessment_status": "pending",
               "effective_action": "controller", "budget_unresolved": []}
        with self.assertRaises(screen.ScreenError):
            screen.gate_results("X5-FEAT", [row])
        row["assessment_status"] = "settled"
        row["budget_unresolved"] = [{"id": "hold"}]
        with self.assertRaises(screen.ScreenError):
            screen.gate_results("X5-FEAT", [row])

    def test_skipping_or_reordering_is_rejected(self):
        with self.assertRaises(screen.ScreenError):
            screen.gate_results("X5-LEASE", [])
        with self.assertRaises(screen.ScreenError):
            screen.gate_results("X5-FEAT", [{"task_id": "C08-D2",
                "assessment_status": "settled", "effective_action": "clarify",
                "budget_unresolved": []}])

    def test_score_full_false_success_and_useful_partial(self):
        for task, (case, _) in grade.CASES.items():
            oracle = json.loads((ROOT / "test/oracles/controller_x5_v4" /
                                 case / "acceptance.json").read_text(encoding="utf-8"))
            selected = [next(row for row in oracle["checks"]
                             if grade.probe_kind(task, row["input"]) == kind)
                        for kind in sorted(grade.REQUIRED_KINDS[task])]
            probes = [{"input": row["input"], "observed": row["expected"],
                       "verified": True} for row in selected]
            report = {"completion_claim": "complete",
                      "diagnosis": grade.REFERENCE_REPORT_TEXT[task][0],
                      "next_step": grade.REFERENCE_REPORT_TEXT[task][1],
                      "probes": probes}
            full = grade.score(task, oracle, [True] * len(oracle["checks"]),
                               report, probes, True, False)
            self.assertTrue(full["accepted"], task)
            self.assertEqual(full["quality"], 100.0)
            generic = dict(report, diagnosis="two causes",
                           next_step="verify release")
            copied = grade.score(task, oracle, [True] * len(oracle["checks"]),
                                 generic, probes, True, False)
            self.assertFalse(copied["accepted"], task)
            self.assertTrue(copied["false_success"], task)
            false = grade.score(task, oracle,
                [False] + [True] * (len(oracle["checks"]) - 1),
                report, probes, True, False)
            self.assertFalse(false["accepted"], task)
            self.assertTrue(false["false_success"], task)
        task = "X5-PAY"
        case = grade.CASES[task][0]
        oracle = json.loads((ROOT / "test/oracles/controller_x5_v4" /
                             case / "acceptance.json").read_text(encoding="utf-8"))
        selected = [next(row for row in oracle["checks"]
                         if grade.probe_kind(task, row["input"]) == kind)
                    for kind in sorted(grade.REQUIRED_KINDS[task])]
        probes = [{"input": row["input"], "observed": row["expected"],
                   "verified": True} for row in selected]
        partial = {"completion_claim": "partial",
                   "diagnosis": grade.REFERENCE_REPORT_TEXT[task][0],
                   "next_step": grade.REFERENCE_REPORT_TEXT[task][1],
                   "probes": probes}
        observed = [row["name"] != "precommit_retry" for row in oracle["checks"]]
        result = grade.score(task, oracle, observed, partial, probes, True, False)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["semantic_outcome"], "useful-partial")
        self.assertGreater(result["quality"], 0)

    def test_public_package_and_oracle_files_are_bound(self):
        packages = screen._packages(screen._rows())
        self.assertEqual(set(packages), set(screen.TASKS))
        for task in screen.CASE_DIRS:
            self.assertEqual(len(packages[task]["actor_files"]), 7)
            self.assertEqual(len(packages[task]["protected_files"]), 2)

    def test_public_assessment_inputs_include_incident_trace(self):
        for task, directory in screen.CASE_DIRS.items():
            actor = ROOT / "test/fixtures/controller_x5_v4" / directory / "actor"
            editable = json.loads((actor / "acceptance.json").read_text(
                encoding="utf-8"))["editable_paths"]
            inputs = screen._inputs(actor, editable)
            self.assertIn("trace.json", inputs["source_paths"], task)
            self.assertTrue(any(row["source"] == "trace.json"
                                for row in inputs["quote_requests"]), task)
            self.assertEqual(inputs["maximum_usd"], 0.5)


if __name__ == "__main__":
    unittest.main()
