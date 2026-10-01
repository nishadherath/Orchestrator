#!/usr/bin/env python3
"""Provider-free X3 inventory and trusted scoring characterisations."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x3_corpus as corpus  # noqa: E402
import controller_x3_grade as grader  # noqa: E402
import controller_x3_language as language  # noqa: E402


class X3Tests(unittest.TestCase):
    def setUp(self):
        self.oracle = json.loads(grader.ORACLE.read_text(encoding="utf-8"))
        self.reference = json.loads((grader.FIXTURE / "variants" / "reference" /
                                     "report.json").read_text(encoding="utf-8"))
        self.partial = json.loads((grader.FIXTURE / "variants" / "partial" /
                                   "report.json").read_text(encoding="utf-8"))

    def _cases(self, failed=()):
        return [{"milestone": row["milestone"], "weight": row["weight"],
                 "passed": index not in failed}
                for index, row in enumerate(self.oracle["cases"])]

    @staticmethod
    def _probes(report):
        return [{"input": row["input"], "observed": row["observed"],
                 "verified": True} for row in report["probes"]]

    def test_reference_alternative_and_useful_partial_scoring(self):
        full = grader.score(self.oracle, self._cases(), self.reference,
                            self._probes(self.reference), True)
        self.assertTrue(full["accepted"])
        self.assertEqual(100, full["quality"])
        partial = grader.score(self.oracle, self._cases({1}), self.partial,
                               self._probes(self.partial), True)
        self.assertFalse(partial["accepted"])
        self.assertEqual("useful-partial", partial["semantic_outcome"])
        self.assertEqual(75, partial["quality"])

    def test_label_copy_and_false_completion_cannot_pass(self):
        forged = [dict(row, observed={"results": [{"status": "committed"}]},
                       verified=False) for row in self._probes(self.reference)]
        result = grader.score(self.oracle, self._cases({0, 1}), self.reference,
                              forged, True)
        self.assertFalse(result["accepted"])
        self.assertEqual(0, result["quality"])
        self.assertTrue(result["critical_violation"])
        self.assertTrue(result["false_success"])

    def test_full_code_with_wrong_diagnosis_is_not_complete(self):
        wrong = dict(self.reference, mechanism="adjacent-network-layer")
        result = grader.score(self.oracle, self._cases(), wrong,
                              self._probes(self.reference), True)
        self.assertFalse(result["accepted"])
        self.assertTrue(result["false_success"])
        self.assertEqual("useful-partial", result["semantic_outcome"])

    def test_outbox_lease_scores_distinct_mechanism_and_useful_partial(self):
        task_id = "C03-D2"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))

        def observations(failed=()):
            return [{"milestone": row["milestone"], "weight": row["weight"],
                     "passed": index not in failed}
                    for index, row in enumerate(oracle["cases"])]

        full = grader.score(oracle, observations(), reference,
                            self._probes(reference), True)
        self.assertTrue(full["accepted"])
        self.assertEqual(100, full["quality"])
        useful = grader.score(oracle, observations({3}), partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual("useful-partial", useful["semantic_outcome"])
        self.assertEqual(92, useful["quality"])
        wrong = dict(reference, mechanism="unfenced-payment-retry")
        rejected = grader.score(oracle, observations(), wrong,
                                self._probes(reference), True)
        self.assertFalse(rejected["accepted"])
        self.assertTrue(rejected["false_success"])

    def test_order_alias_probes_require_account_separation(self):
        task_id = "C01-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        self.assertEqual(100, complete["quality"])
        cases[3]["passed"] = False
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(92, useful["quality"])
        forged = self._probes(reference)
        forged[1] = dict(forged[1], observed={"settled": ["PO-0008"], "pending": []})
        wrong = grader.score(oracle, [dict(row, passed=True) for row in cases],
                             reference, forged, True)
        self.assertFalse(wrong["accepted"])

    def test_migration_probe_requires_fallback_and_precedence(self):
        task_id = "C02-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        self.assertEqual(100, complete["quality"])
        cases[3]["passed"] = False
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(92, useful["quality"])
        altered = self._probes(reference)
        altered[1] = dict(altered[1], observed={"values": [
            {"id": "probe-b", "value": 21}]})
        wrong = grader.score(oracle, [dict(row, passed=True) for row in cases],
                             reference, altered, True)
        self.assertFalse(wrong["accepted"])

    def test_tenant_cache_probe_requires_separation_and_owner_hit(self):
        task_id = "C04-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        self.assertEqual(100, complete["quality"])
        cases[3]["passed"] = False
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(92, useful["quality"])
        forged = self._probes(reference)
        forged[0] = dict(forged[0], observed={"results": [
            {"status": "stored"}, {"status": "hit", "value": True}]})
        wrong = grader.score(oracle, [dict(row, passed=True) for row in cases],
                             reference, forged, True)
        self.assertFalse(wrong["accepted"])

    def test_local_slice_partial_scores_above_confident_baseline(self):
        task_id = "N02-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        for row in cases[2:]:
            row["passed"] = False
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(76, useful["quality"])
        baseline = grader.score(oracle,
            [dict(row, passed=index in {3, 4}) for index, row in enumerate(cases)],
            json.loads((fixture / "actor" / "report.json").read_text(encoding="utf-8")),
            [], True)
        self.assertFalse(baseline["accepted"])
        self.assertTrue(baseline["false_success"])
        self.assertEqual(16, baseline["quality"])

    def test_missing_operator_fact_accepts_clarification_without_edit(self):
        task_id = "N03-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        accepted = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(accepted["accepted"])
        self.assertEqual("accepted-clarification", accepted["semantic_outcome"])
        self.assertEqual(100, accepted["quality"])
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(72.5, useful["quality"])
        duplicate = grader.score(oracle, cases, reference,
            [self._probes(reference)[0]] * 2, True)
        self.assertFalse(duplicate["accepted"])
        changed = grader.score(oracle, cases, reference,
                               self._probes(reference), True,
                               actor_edit_violation=True)
        self.assertFalse(changed["accepted"])
        self.assertTrue(changed["critical_violation"])
        self.assertEqual(0, changed["quality"])

    def test_region_decision_requires_two_observations_and_no_edit(self):
        task_id = "N03-D2"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        report = json.loads((fixture / "variants" / "reference" /
                             "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        accepted = grader.score(oracle, cases, report,
                                self._probes(report), True)
        self.assertTrue(accepted["accepted"])
        self.assertEqual("accepted-clarification", accepted["semantic_outcome"])
        duplicate = grader.score(oracle, cases, report,
                                 [self._probes(report)[0]] * 2, True)
        self.assertFalse(duplicate["accepted"])
        changed = grader.score(oracle, cases, report,
                               self._probes(report), True,
                               actor_edit_violation=True)
        self.assertEqual(0, changed["quality"])

    def test_clock_skew_requires_both_causal_directions(self):
        task_id = "C06-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        self.assertEqual(100, complete["quality"])
        cases[3]["passed"] = False
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(92, useful["quality"])
        wrong = grader.score(oracle, [dict(row, passed=True) for row in cases],
                             reference, [self._probes(reference)[0]] * 2, True)
        self.assertFalse(wrong["accepted"])

    def test_cross_consumer_money_probe_requires_exact_decimal_result(self):
        task_id = "C07-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        self.assertEqual({"aggregate", "binary-float"},
            {grader._money_probe_kind(row["input"]) for row in reference["probes"]})
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        self.assertEqual(100, complete["quality"])
        cases[3]["passed"] = False
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(92, useful["quality"])
        forged = self._probes(reference)
        forged[1] = dict(forged[1], observed={"ledger": "1.23", "statement": "1.23"})
        wrong = grader.score(oracle, [dict(row, passed=True) for row in cases],
                             reference, forged, True)
        self.assertFalse(wrong["accepted"])

    def test_contradictory_lock_order_requires_clarification_and_no_edit(self):
        task_id = "C08-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        self.assertEqual("accepted-clarification", complete["semantic_outcome"])
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(72.5, useful["quality"])
        changed = grader.score(oracle, cases, reference,
                               self._probes(reference), True,
                               actor_edit_violation=True)
        self.assertFalse(changed["accepted"])
        self.assertEqual(0, changed["quality"])

    def test_streaming_join_stress_is_distinct_from_small_case(self):
        task_id = "C05-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((fixture / "variants" / "reference" /
                                "report.json").read_text(encoding="utf-8"))
        partial = json.loads((fixture / "variants" / "partial" /
                              "report.json").read_text(encoding="utf-8"))
        stress = grader._case_input(task_id, oracle["cases"][3]["input"])
        self.assertEqual(64, len(stress["left"]))
        self.assertEqual(64, len(stress["right"]))
        self.assertTrue(all(row["time"] - stress["left"][index]["time"] == 50
                            for index, row in enumerate(stress["right"])))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": True} for row in oracle["cases"]]
        complete = grader.score(oracle, cases, reference,
                                self._probes(reference), True)
        self.assertTrue(complete["accepted"])
        cases[3]["passed"] = False
        useful = grader.score(oracle, cases, partial,
                              self._probes(partial), True)
        self.assertFalse(useful["accepted"])
        self.assertEqual(92, useful["quality"])

    def test_inventory_exposes_pending_work_and_rejects_public_edit(self):
        result = corpus.inventory()
        self.assertEqual(48, result["required_tasks"])
        self.assertEqual(48, result["ready_tasks"] + result["pending_tasks"])
        self.assertEqual(48, len({row["task_id"] for row in result["tasks"]}))
        self.assertIn("C03-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C03-D2", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C01-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C02-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C04-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("N02-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("N03-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C06-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C07-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C08-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("C05-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("N01-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("N04-D1", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("N02-D2", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("N03-D2", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        self.assertIn("N01-D2", {row["task_id"] for row in result["tasks"]
                                     if row["status"] == "ready"})
        with tempfile.TemporaryDirectory(prefix="controller-x3-inventory-") as raw:
            shutil.copytree(corpus.ACTORS, Path(raw), dirs_exist_ok=True)
            destination = Path(raw) / "development" / grader.TASK_ID
            bad = destination / "variants" / "reference" / "public_check.py"
            bad.write_text("# weakened\n", encoding="utf-8")
            with patch.object(corpus, "ACTORS", Path(raw)):
                with self.assertRaisesRegex(corpus.CorpusError, "editable boundary"):
                    corpus.inventory()

    def test_negative_control_rename_and_manifest_partial_progress(self):
        for task_id, missing_indices, partial_score in (
                ("N01-D1", (3,), 92), ("N04-D1", (1,), 88),
                ("N04-D2", (2,), 88), ("C01-D2", (3,), 88),
                ("C02-D2", (3,), 88),
                ("C04-D2", (3,), 88),
                ("C06-D2", (3,), 88),
                ("C05-D2", (3,), 88),
                ("N02-D2", (2, 3), 80),
                ("N01-D2", (0, 3, 4), 61)):
            with self.subTest(task_id=task_id):
                fixture = (ROOT / "test" / "fixtures" / "controller_x3" /
                           "development" / task_id)
                oracle = json.loads((ROOT / "test" / "oracles" /
                                     "controller_x3" / f"{task_id}.json")
                                    .read_text(encoding="utf-8"))
                reference = json.loads((fixture / "variants" / "reference" /
                                        "report.json").read_text(encoding="utf-8"))
                partial = json.loads((fixture / "variants" / "partial" /
                                      "report.json").read_text(encoding="utf-8"))
                cases = [{"milestone": row["milestone"], "weight": row["weight"],
                          "passed": True} for row in oracle["cases"]]
                complete = grader.score(oracle, cases, reference,
                                        self._probes(reference), True)
                self.assertTrue(complete["accepted"])
                self.assertEqual(100, complete["quality"])
                for missing_index in missing_indices:
                    cases[missing_index]["passed"] = False
                useful = grader.score(oracle, cases, partial,
                                      self._probes(partial), True)
                self.assertFalse(useful["accepted"])
                self.assertEqual(partial_score, useful["quality"])
                self.assertEqual("useful-partial", useful["semantic_outcome"])

    def test_prose_reports_are_not_forced_to_hidden_slug_strings(self):
        self.assertEqual(set(grader.RUBRICS), set(language.LANGUAGE))
        for task_id, mechanism, next_step in (
                ("N01-D2",
                 "The client and scheduler still read the legacy timeout key in milliseconds.",
                 "Replay new-key overrides through both readers before rollout."),
                ("N03-D2", "The approved target region for pilot is missing.",
                 "Ask the operator for an approved region before editing routing.")):
            with self.subTest(task_id=task_id):
                fixture = (ROOT / "test" / "fixtures" / "controller_x3" /
                           "development" / task_id)
                oracle = json.loads((ROOT / "test" / "oracles" /
                                     "controller_x3" / f"{task_id}.json")
                                    .read_text(encoding="utf-8"))
                report = json.loads((fixture / "variants" / "reference" /
                                     "report.json").read_text(encoding="utf-8"))
                report["mechanism"] = mechanism
                report["next_step"] = next_step
                cases = [{"milestone": row["milestone"], "weight": row["weight"],
                          "passed": True} for row in oracle["cases"]]
                observed = grader.score(oracle, cases, report,
                                        self._probes(report), True)
                self.assertTrue(observed["accepted"])
                self.assertEqual(100, observed["quality"])
                report["mechanism"] = "looks fine"
                report["next_step"] = "ship it"
                vague = grader.score(oracle, cases, report,
                                     self._probes(report), True)
                self.assertFalse(vague["accepted"])

    def test_unanticipated_bounded_probe_is_kept_for_evidence(self):
        report = json.loads(json.dumps(self.reference))
        report["probes"].append({"input": {"new_case": "actor-chosen"},
                                 "observed": {"error": "unknown"}})
        self.assertIsNotNone(grader._report(report, grader.TASK_ID))
        report["probes"][-1]["input"] = {"large": "x" * 5000}
        self.assertIsNone(grader._report(report, grader.TASK_ID))

    def test_noncausal_actor_probe_does_not_replace_required_diagnosis(self):
        report = json.loads(json.dumps(self.reference))
        report["probes"][1] = {"input": {"actor_selected": "unrelated"},
                                "observed": {"note": "observed"}}
        self.assertIsNotNone(grader._report(report, grader.TASK_ID))
        verified = self._probes(report)
        result = grader.score(self.oracle, self._cases(), report, verified, True)
        self.assertFalse(result["accepted"])
        self.assertEqual(0, result["components"]["D"])
        self.assertEqual(1, result["components"]["E"])

    def test_each_current_rubric_accepts_a_plain_language_description(self):
        examples = {
            "N04-R2": ("The generated fixture pair is stale against its source.",
                        "Rebuild both fixtures and check reproducibility.",
                        "Regenerate the worker fixture and recheck the pair."),
            "N04-R1": ("The feature disable audit step is omitted.",
                        "Verify flag, audit, and idempotency.",
                        "Append the audit event and recheck idempotency."),
            "N03-R2": ("The approved destructive cutover time is absent.",
                        "Await the approved UTC cutover time.", None),
            "N03-R1": ("The minimum client version for mandatory trace is missing.",
                        "Await the minimum version and older client decision.",
                        None),
            "N02-R2": ("Mutable default lists leak across independent calls.",
                        "Replay independent heading and footer calls.",
                        "Remove the footer shared default and recheck."),
            "N02-R1": ("The strict threshold excludes the equality boundary.",
                        "Recheck boundary and adjacent values.",
                        "Tighten the adjacent value without losing the boundary."),
            "N01-R2": ("The generated header is stale because the generator is hardcoded.",
                        "Regenerate the header and verify schema variation.",
                        "Replace the hardcoded generator and recheck the header."),
            "N01-R1": ("Stale legacy package import paths remain active.",
                        "Exercise API, batch, and export contracts.",
                        "Migrate the batch import and remove the legacy export."),
            "C08-R2": ("Same-term dual writer and unfenced expired write.",
                        "Replay overlap and post-expiry takeover.",
                        "Verify post-expiry takeover."),
            "C08-R1": ("Unbounded replay buffer emits in arrival order.",
                        "Replay capacity and gap-close ordering.",
                        "Verify buffered drain after gap close."),
            "C07-R2": ("Transport sequence watermark overrides the state revision.",
                        "Replay stale high and later valid revision traces.",
                        "Verify later valid revision after a stale watermark."),
            "C07-R1": ("Unicode character count shifts the following frame boundary.",
                        "Replay Unicode single and following-frame boundaries.",
                        "Verify following-frame decoding."),
            "C06-R2": ("New reader lacks old row fallback and new writer omits legacy projection.",
                        "Replay old rows and old-reader new writes.",
                        "Verify old-reader access to new writes."),
            "C06-R1": ("Broad cache eviction triggers uncoalesced refill loads.",
                        "Replay unaffected keys and burst refill waves.",
                        "Verify hot-key refill coalescing and stagger."),
            "C05-R2": ("Little endian byte order breaks the published big endian frame for the legacy reader.",
                        "Replay legacy and current empty frames.",
                        "Verify current decoder empty frame handling."),
            "C05-R1": ("Pending queue depth is confused with batch size.",
                        "Replay burst and drain traces before rollout.",
                        "Verify configured capacity of three."),
            "C04-R2": ("Pooled connection tenant session state survives return.",
                        "Replay cross-tenant checkout and error recovery.",
                        "Verify connection recovery after an error."),
            "C04-R1": ("Object ID lookup misses the tenant ownership check.",
                        "Replay foreign and owner archived lookups before rollout.",
                        "Verify owner archived report lookup."),
            "C03-R2": ("The sequence watermark is confused with delivery identity.",
                        "Replay duplicate and out-of-order deliveries.",
                        "Verify lower-sequence distinct deliveries."),
            "C03-R1": ("A stale worker fence can commit after lease owner transfer.",
                        "Replay overlap and owner transfer before rollout.",
                        "Verify the new owner completion after transfer."),
            "C02-R2": ("Checkpoint overlap duplicates an add, while an ignored tombstone resurrects a deleted key.",
                        "Replay checkpoint and tombstone traces before rollout.",
                        "Verify prefix tombstones before rollout."),
            "C02-R1": ("Shadow-only writes leave the rollback reader stale.",
                        "Replay cutover and rollback readers.",
                        "Verify the cutover rollback reader."),
            "C01-R2": ("The stale index overrides the authoritative row revision.",
                        "Replay updated rows and tombstones.",
                        "Verify the latest tombstone."),
            "C01-R1": ("Sequence deduplication is scoped too broadly across feeds.",
                        "Replay cross-feed and new-epoch sequences.",
                        "Verify new-epoch sequence reuse."),
            "C05-D2": ("The index page selector fetches the unbounded whole index.",
                        "Measure offset and narrow pages before rollout.",
                        "Verify the narrow page read bound."),
            "C06-D2": ("A retry storm fills pool slots and starves foreground work.",
                        "Replay retry storms and foreground surges.",
                        "Verify retry progress during a foreground surge."),
            "C07-D2": ("The UTC date is used instead of the Sydney reporting window.",
                        "Replay winter and daylight-saving boundaries.",
                        "Verify the daylight-saving offset."),
            "C08-D2": ("The immutable version-one API contract conflicts with the requested field.",
                        "Ask the owner for a compatible versioning path.", None),
            "C04-D2": ("Retry forwarding drops tenant and trace job context.",
                        "Replay tenant and trace retries before rollout.",
                        "Verify trace propagation on retry."),
            "C02-D2": ("The envelope rewrite drops metadata fields.",
                        "Replay unknown fields before rollout.",
                        "Verify unknown extension preservation."),
            "C01-D2": ("Concatenating namespace and token aliases cache keys.",
                        "Replay punctuation alias traces.",
                        "Verify delimiter punctuation with framing."),
            "N04-D2": ("The staged key rotation only accepts the old identifier.",
                        "Verify both identifiers and test the signer.",
                        "Switch the signer to green."),
            "C01-D1": ("Versioned order identifiers are joined without normalizing aliases.",
                        "Replay cross-account alias cases.", "Check prefix collisions."),
            "C02-D1": ("The migration backfill overwrites newer current values.",
                        "Verify mixed-version rows before cutover.",
                        "Check zero-valued current rows."),
            "C03-D1": ("Committed retries lack a durable idempotency receipt.",
                        "Replay payment retries before cutover.",
                        "Verify conflicting payloads."),
            "C03-D2": ("The outbox delivery lease is not fenced against stale workers.",
                        "Replay lease expiry with overlapping claims.",
                        "Check duplicate acknowledgements."),
            "C04-D1": ("Tenant is missing from the feature cache key.",
                        "Replay cross-tenant cache traces.",
                        "Check same-tenant updates."),
            "C05-D1": ("The window join retains unbounded Cartesian state.",
                        "Replay sparse streams and measure the cap.",
                        "Measure bounded live state."),
            "C06-D1": ("The worker clock controls lease expiry.",
                        "Compare server time against queue lag.",
                        "Check exact server expiry."),
            "C07-D1": ("Decimal rounding differs between ledger and statement consumers.",
                        "Reconcile ledger and statement totals before posting.",
                        "Test negative refunds."),
            "C08-D1": ("The two lock order requirements conflict.",
                        "Ask the owner for a lock order decision.", None),
            "N01-D1": ("The old format_cents symbol remains in stale imports.",
                        "Run import and negative-value checks.",
                        "Remove old imports."),
            "N01-D2": ("The client reads the legacy timeout key in milliseconds.",
                        "Replay new-key overrides.",
                        "Remove the legacy key and update readers."),
            "N02-D1": ("The inclusive slice bound returns one extra item.",
                        "Run boundary limit tests.", "Check interior bounds."),
            "N02-D2": ("The profile dereference fails on null values.",
                        "Run null and missing-key checks.",
                        "Guard missing email keys."),
            "N03-D1": ("The retention duration is missing from operator approval.",
                        "Ask the operator for retention days.", None),
            "N03-D2": ("The approved target region for pilot is missing.",
                        "Ask the operator for an approved region.", None),
            "N04-D1": ("The audit manifest pin is stale.",
                        "Verify both manifest pins.", "Update the audit pin."),
        }
        self.assertEqual(set(grader.RUBRICS), set(examples))
        for task_id, (mechanism, complete, partial) in examples.items():
            with self.subTest(task_id=task_id):
                oracle = json.loads((ROOT / "test" / "oracles" /
                                     "controller_x3" / f"{task_id}.json")
                                    .read_text(encoding="utf-8"))
                rubric = grader.RUBRICS[task_id]
                self.assertTrue(language.matches(
                    task_id, "mechanism", mechanism, oracle["diagnosis"]))
                self.assertTrue(language.matches(
                    task_id, "complete", complete, rubric["complete_next_step"]))
                if partial is not None:
                    self.assertTrue(language.matches(
                        task_id, "partial", partial, rubric["partial_next_step"]))

    def test_obvious_denial_cannot_pass_by_including_keywords(self):
        task_id = "C04-D1"
        oracle = json.loads((ROOT / "test" / "oracles" /
                             "controller_x3" / f"{task_id}.json")
                            .read_text(encoding="utf-8"))
        self.assertFalse(language.matches(
            task_id, "mechanism",
            "There is no tenant cache key issue; it is already correct.",
            oracle["diagnosis"]))

    def test_confident_label_copy_cannot_claim_partial_next_step_credit(self):
        task_id = "N02-D1"
        fixture = ROOT / "test" / "fixtures" / "controller_x3" / "development" / task_id
        oracle = json.loads((ROOT / "test" / "oracles" / "controller_x3" /
                             f"{task_id}.json").read_text(encoding="utf-8"))
        report = json.loads((fixture / "variants" / "label_copy" /
                             "report.json").read_text(encoding="utf-8"))
        cases = [{"milestone": row["milestone"], "weight": row["weight"],
                  "passed": index >= 3}
                 for index, row in enumerate(oracle["cases"])]
        probes = [dict(row, verified=False) for row in report["probes"]]
        observed = grader.score(oracle, cases, report, probes, True)
        self.assertFalse(observed["accepted"])
        self.assertEqual(0, observed["components"]["N"])
        self.assertEqual(16, observed["quality"])


if __name__ == "__main__":
    unittest.main()
