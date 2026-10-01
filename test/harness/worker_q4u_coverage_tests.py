"""Provider-free Q4U public-evidence and prospective policy checks."""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_coverage import CoverageError, assess, decision, LOW, MEDIUM  # noqa: E402


def citation(path: str, text: str, line: int = 1) -> dict:
    return {"path": path, "line": line, "text": text,
            "file_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def sample(coverage: str = "partial", *, issue: str = "Memory must stay bounded.",
           check: str = "assert peek() == 1", change: bool = True) -> tuple[dict, dict, dict]:
    issues = {"ISSUE.md": issue}
    checks = {"test_public.py": check}
    row = {"id": "bounded_memory", "coverage": coverage,
           "issue_citation": citation("ISSUE.md", issue),
           "check_citations": [citation("test_public.py", check)],
           "gap": "No retained-memory assertion" if coverage != "direct" else ""}
    facts = {"task_kind": "implementation", "cross_component": False,
             "change_required": change, "criteria": [row]}
    return facts, issues, checks


def route(assessment: dict, policy: str, phase: str = "initial",
          outcome: str | None = None, **kwargs: object) -> dict:
    options = {"supported_cells": {LOW, MEDIUM}, "remaining_usd": 4.0,
               "call_ceiling_usd": 2.0, "budget_enforced": True}
    options.update(kwargs)
    return decision(assessment, policy=policy, phase=phase, low_outcome=outcome,
                    **options)


class CoverageTests(unittest.TestCase):
    def test_partial_requires_public_citations_and_gap(self):
        facts, issues, checks = sample()
        value = assess(facts, issue_files=issues, check_files=checks)
        self.assertEqual("partial", value["verification_coverage"])
        self.assertEqual("q4u-coverage-v1", value["policy"])
        facts["criteria"][0]["check_citations"][0]["text"] = "unrelated assertion"
        with self.assertRaises(CoverageError):
            assess(facts, issue_files=issues, check_files=checks)

    def test_direct_needs_check_unknown_abstains_and_hidden_path_rejected(self):
        facts, issues, checks = sample("direct")
        facts["criteria"][0]["check_citations"] = []
        with self.assertRaises(CoverageError):
            assess(facts, issue_files=issues, check_files=checks)
        facts["criteria"][0]["coverage"] = "unknown"
        facts["criteria"][0]["gap"] = "Cannot map check to resource bound"
        value = assess(facts, issue_files=issues, check_files=checks)
        self.assertEqual("unknown", value["verification_coverage"])
        with self.assertRaises(CoverageError):
            assess(facts, issue_files=issues, check_files={"oracles/test_public.py": "x"})

    def test_rule_table_and_conditional_cost(self):
        facts, issues, checks = sample()
        a = assess(facts, issue_files=issues, check_files=checks)
        self.assertEqual(LOW, route(a, "b0")["action"])
        self.assertEqual(LOW, route(a, "cross_component_medium")["action"])
        self.assertEqual(LOW, route(a, "coverage_repair")["action"])
        self.assertEqual(MEDIUM, route(a, "coverage_repair", "after_low", "no_change")["action"])
        self.assertEqual(MEDIUM, route(a, "coverage_repair", "after_low", "verification_failed")["action"])
        self.assertEqual("stop", route(a, "coverage_repair", "after_low", "accepted")["action"])
        self.assertEqual("stop", route(a, "coverage_repair", "after_low", "blocked")["action"])
        self.assertEqual(2.0, route(a, "coverage_repair", "after_low", "no_change")["reserved_usd"])
        self.assertEqual(0, route(a, "coverage_repair", "after_low", "accepted")["maximum_new_calls"])

    def test_uncertainty_no_change_control_and_cross_component(self):
        facts, issues, checks = sample("unknown", change=False)
        a = assess(facts, issue_files=issues, check_files=checks)
        self.assertEqual(LOW, route(a, "coverage_repair", "after_low", "no_change")["action"])
        facts["cross_component"] = True
        a = assess(facts, issue_files=issues, check_files=checks)
        self.assertEqual(MEDIUM, route(a, "cross_component_medium")["action"])
        self.assertEqual(LOW, route(a, "coverage_repair")["action"])

    def test_host_and_budget_abstention(self):
        facts, issues, checks = sample()
        a = assess(facts, issue_files=issues, check_files=checks)
        row = route(a, "coverage_repair", "after_low", "no_change",
                    supported_cells={LOW})
        self.assertEqual((LOW, "abstain_medium_unavailable"), (row["action"], row["reason"]))
        self.assertEqual("call_ceiling_unfunded", route(
            a, "coverage_repair", remaining_usd=1.0)["reason"])
        self.assertEqual("budget_not_enforced", route(
            a, "coverage_repair", budget_enforced=False)["reason"])
        self.assertEqual("host_unsupported", route(
            a, "coverage_repair", supported_cells=set())["reason"])

    def test_policy_rejects_assessment_changed_after_validation(self):
        facts, issues, checks = sample("direct")
        a = assess(facts, issue_files=issues, check_files=checks)
        a["verification_coverage"] = "partial"
        with self.assertRaises(CoverageError):
            route(a, "coverage_repair", "after_low", "no_change")

    def test_wording_stability_without_task_identifier_rule(self):
        first = sample(issue="Memory must stay bounded.")
        second = sample(issue="Retained memory cannot grow after repeated peeks.")
        a = assess(first[0], issue_files=first[1], check_files=first[2])
        b = assess(second[0], issue_files=second[1], check_files=second[2])
        self.assertNotEqual(a["public_file_sha256"], b["public_file_sha256"])
        self.assertEqual(route(a, "coverage_repair", "after_low", "no_change"),
                         route(b, "coverage_repair", "after_low", "no_change"))

    def test_s05_public_evidence_is_partial_development_diagnosis(self):
        actor = ROOT / "test/fixtures/worker_q4s_public/S05/actor"
        issue = (actor / "ISSUE.md").read_text(encoding="utf-8")
        check = (actor / "public_check.py").read_text(encoding="utf-8")

        def ref(path: str, content: str, line: int) -> dict:
            return {"path": path, "line": line,
                    "text": content.splitlines()[line - 1],
                    "file_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}

        facts = {"task_kind": "implementation", "cross_component": False,
                 "change_required": True,
                 "criteria": [{"id": "retained_memory", "coverage": "partial",
                               "issue_citation": ref("ISSUE.md", issue, 4),
                               "check_citations": [ref("public_check.py", check, 10)],
                               "gap": "Five peeks check behaviour, not retained memory"}]}
        a = assess(facts, issue_files={"ISSUE.md": issue},
                   check_files={"public_check.py": check})
        self.assertEqual("partial", a["verification_coverage"])
        self.assertEqual(LOW, route(a, "coverage_repair")["action"])
        self.assertEqual(MEDIUM, route(a, "coverage_repair", "after_low", "no_change")["action"])


if __name__ == "__main__":
    unittest.main()
