#!/usr/bin/env python3
"""Provider-free checks for the Q4 quality and report contract."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import model_registry  # noqa: E402
from worker_adapter import WorkerAdapter, WorkerRequest, digest  # noqa: E402
from worker_q4_adapter import EvaluationWorkerAdapter  # noqa: E402
from worker_quality_v2 import (QualityContractError, grade, parse_report,
                               report_evidence, validate_rubric)  # noqa: E402


def report(status="completed", checks=None):
    return {"status": status, "diagnosis": "The cache writes a stale value.",
            "evidence": ["public_check.py reproduces the mismatch"],
            "checks": checks if checks is not None else
                      [{"command": "python3 -B public_check.py", "outcome": "passed"}],
            "remaining": [] if status == "completed" else ["cache identity"],
            "clarification": None}


def rubric():
    def row(identifier, category, weight, *, mandatory=True, critical=False,
            comparator="semantic", public_exact=False):
        return {"id": identifier, "category": category, "weight": weight,
                "mandatory": mandatory, "critical": critical,
                "comparator": comparator,
                "public_obligation": f"Public obligation for {identifier}",
                "public_exact": public_exact}
    return {"schema_version": 2, "task_sha256": "a" * 64,
            "public_spec_sha256": "b" * 64,
            "predicates": [row("behaviour-a", "behaviour", 30),
                           row("behaviour-b", "behaviour", 30),
                           row("invariant", "invariant", 20, critical=True),
                           row("diagnosis", "diagnosis", 10, mandatory=False),
                           row("report", "report", 10, mandatory=False)]}


def observations(**changes):
    value = {identifier: {"passed": True, "evidence": f"root evidence {identifier}"}
             for identifier in ("behaviour-a", "behaviour-b", "invariant",
                                "diagnosis", "report")}
    for key, passed in changes.items():
        value[key.replace("_", "-")] = {"passed": passed,
                                          "evidence": f"root evidence {key}"}
    return value


def binding():
    return {"invocation_id": "inv", "revision_id": "rev",
            "final_revision_sha256": "c" * 64, "stream_sha256": "d" * 64,
            "task_sha256": "a" * 64, "prompt_sha256": "e" * 64,
            "requested_cell": "worker-sonnet-low"}


class QualityContractTests(unittest.TestCase):
    def test_rubric_requires_public_mapping_and_exact_weight_split(self):
        validate_rubric(rubric())
        for mutate in ("weights", "exact", "duplicate", "critical-report"):
            changed = copy.deepcopy(rubric())
            if mutate == "weights":
                changed["predicates"][0]["weight"] = 29
            elif mutate == "exact":
                changed["predicates"][0]["comparator"] = "exact_text"
            elif mutate == "duplicate":
                changed["predicates"][1]["id"] = "behaviour-a"
            else:
                changed["predicates"][-1]["critical"] = True
            with self.subTest(mutate=mutate), self.assertRaises(QualityContractError):
                validate_rubric(changed)

    def test_report_schema_rejects_coercion_extra_fields_and_oversize(self):
        self.assertEqual("completed", parse_report(json.dumps(report()))["status"])
        failures = [json.dumps({**report(), "extra": True}),
                    json.dumps({**report(), "status": "success"}),
                    json.dumps({**report(), "checks": ["looks good"]}),
                    json.dumps({**report(), "diagnosis": "x" * 17000}),
                    "not json"]
        for raw in failures:
            with self.subTest(raw=raw[:20]), self.assertRaises(QualityContractError):
                parse_report(raw)

    def test_missing_report_preserves_executable_score_without_acceptance(self):
        record = report_evidence(None, binding())
        result = grade(rubric(), observations(), record, root_state="accepted",
                       execution_checks={"python3 -B public_check.py": True},
                       expected_binding=binding())
        self.assertEqual(80, result["quality"])
        self.assertTrue(result["behaviour_accepted"])
        self.assertFalse(result["hidden_accepted"])
        self.assertTrue(result["root_acceptance_gap"])
        self.assertFalse(result["unsupported_completion"])
        self.assertEqual("worker-missing", result["report_observability"])

    def test_honest_partial_differs_from_unsupported_completion(self):
        partial = report_evidence(json.dumps(report("partial")), binding())
        completed = report_evidence(json.dumps(report("completed")), binding())
        failed = observations(behaviour_b=False)
        honest = grade(rubric(), failed, partial, root_state="accepted",
                       execution_checks={"python3 -B public_check.py": True},
                       expected_binding=binding())
        false_completion = grade(rubric(), failed, completed, root_state="accepted",
                                 execution_checks={"python3 -B public_check.py": True},
                                 expected_binding=binding())
        self.assertFalse(honest["unsupported_completion"])
        self.assertTrue(false_completion["unsupported_completion"])
        self.assertEqual(honest["quality"], false_completion["quality"])

    def test_contradicted_test_claim_is_not_inferred_from_unknown(self):
        record = report_evidence(json.dumps(report()), binding())
        contradicted = grade(rubric(), observations(), record, root_state="accepted",
                             execution_checks={"python3 -B public_check.py": False},
                             expected_binding=binding())
        unknown = grade(rubric(), observations(), record, root_state="accepted",
                        execution_checks={}, expected_binding=binding())
        self.assertTrue(contradicted["unsupported_completion"])
        self.assertEqual(["python3 -B public_check.py"],
                         contradicted["contradicted_check_claims"])
        self.assertFalse(unknown["unsupported_completion"])
        self.assertTrue(unknown["hidden_accepted"])

    def test_critical_error_and_transport_fault_stay_separate(self):
        present = report_evidence(json.dumps(report("partial")), binding())
        critical = grade(rubric(), observations(invariant=False), present,
                         root_state="partial", execution_checks={},
                         expected_binding=binding())
        invalid = report_evidence(json.dumps(report()), binding(), transport_valid=False)
        transport = grade(rubric(), observations(), invalid, root_state="partial",
                          execution_checks={}, expected_binding=binding())
        self.assertTrue(critical["critical_error"])
        self.assertTrue(critical["critical_coverage"])
        self.assertFalse(critical["inconclusive"])
        self.assertFalse(transport["critical_error"])
        self.assertTrue(transport["inconclusive"])

    def test_wrong_revision_binding_and_changed_report_bytes_fail_closed(self):
        record = report_evidence(json.dumps(report()), binding())
        wrong = {**binding(), "revision_id": "another"}
        with self.assertRaises(QualityContractError):
            grade(rubric(), observations(), record, root_state="accepted",
                  execution_checks={}, expected_binding=wrong)
        changed = copy.deepcopy(record)
        changed["raw_utf8"] = changed["raw_utf8"].replace("stale", "fresh")
        with self.assertRaises(QualityContractError):
            grade(rubric(), observations(), changed, root_state="accepted",
                  execution_checks={}, expected_binding=binding())


class EvaluationAdapterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="q4-report-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "output.txt").write_text("revision", encoding="utf-8")
        self.config = self.root / "mcp.json"
        self.config.write_text(json.dumps({"mcpServers": {"graft": {
            "command": sys.executable,
            "args": ["graft", "mcp", "${CLAUDE_PROJECT_DIR:-.}"]}}}),
            encoding="utf-8")
        self.request = WorkerRequest(self.root, "Repair cache", ("output.txt",),
                                     "worker-sonnet-low", 1.0, "Q4",
                                     admission_token="token", invocation_id="inv",
                                     revision_id="rev", decision_digest="decision",
                                     intent_digest="intent")

    def stream(self, *, result_text=None, invalid=False):
        model = model_registry.resolve_cell("worker-sonnet-low")["cli_model"]
        rows = [{"type": "assistant", "parent_tool_use_id": None,
                 "message": {"model": model, "content": []}},
                {"type": "result", "subtype": "success", "result": result_text,
                 "total_cost_usd": 0.1,
                 "usage": {"input_tokens": 1, "output_tokens": 2},
                 "modelUsage": {model: {"costUSD": 0.1}}}]
        prefix = "broken\n" if invalid else ""
        return prefix + "\n".join(json.dumps(row) for row in rows) + "\n"

    def adapter(self, stdout):
        return EvaluationWorkerAdapter(self.config, lambda cmd, cwd, env, timeout:
            subprocess.CompletedProcess(cmd, 0, stdout, ""))

    def test_evaluation_adapter_binds_only_final_report(self):
        receipt = self.adapter(self.stream(result_text=json.dumps(report()))).run(self.request)
        evidence = receipt["evaluation_report"]
        self.assertEqual("present", evidence["observability"])
        self.assertEqual("inv", evidence["binding"]["invocation_id"])
        self.assertEqual("rev", evidence["binding"]["revision_id"])
        self.assertEqual("worker-sonnet-low", evidence["binding"]["requested_cell"])
        self.assertEqual(digest(evidence), receipt["evaluation_report_digest"])
        self.assertNotIn("diagnosis", json.dumps({key: value for key, value in receipt.items()
                                                  if key != "evaluation_report"}))

    def test_base_adapter_does_not_retain_model_text(self):
        base = WorkerAdapter(self.config, lambda cmd, cwd, env, timeout:
            subprocess.CompletedProcess(cmd, 0,
                                        self.stream(result_text=json.dumps(report())), ""))
        receipt = base.run(self.request)
        self.assertNotIn("evaluation_report", receipt)
        self.assertNotIn("diagnosis", json.dumps(receipt))

    def test_missing_malformed_and_invalid_transport_are_distinct(self):
        missing = self.adapter(self.stream(result_text=None)).run(self.request)
        malformed = self.adapter(self.stream(result_text="not json")).run(self.request)
        invalid = self.adapter(self.stream(result_text=json.dumps(report()), invalid=True)).run(
            self.request)
        self.assertEqual("worker-missing", missing["evaluation_report"]["observability"])
        self.assertEqual("worker-malformed", malformed["evaluation_report"]["observability"])
        self.assertEqual("transport-invalid", invalid["evaluation_report"]["observability"])

    def test_timeout_and_unknown_cost_do_not_become_stopped_success(self):
        timed = EvaluationWorkerAdapter(self.config, lambda cmd, cwd, env, timeout:
            (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd, timeout)))
        timeout = timed.run(self.request)
        no_cost = self.adapter(self.stream(result_text=json.dumps(report())).replace(
            ', "total_cost_usd": 0.1', '')).run(self.request)
        self.assertFalse(timeout["terminal"])
        self.assertFalse(timeout["writer_stopped"])
        self.assertEqual("transport-invalid", timeout["evaluation_report"]["observability"])
        self.assertFalse(no_cost["terminal"])
        self.assertFalse(no_cost["writer_stopped"])
        self.assertIsNone(no_cost["cost_usd"])


if __name__ == "__main__":
    unittest.main()
