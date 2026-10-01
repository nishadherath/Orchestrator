#!/usr/bin/env python3
"""X3 public-only assessment and provenance boundary tests."""
from __future__ import annotations

import shutil
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_public_assessment as public  # noqa: E402
import controller_control  # noqa: E402
import controller_policy  # noqa: E402

ACTOR = ROOT / "test" / "fixtures" / "controller_x3" / "development" / "C03-D1" / "actor"
SOURCES = ["issue.md", "public_check.py"]
QUOTES = [{"source": "issue.md", "quote": "same idempotency key"},
          {"source": "public_check.py", "quote": "does not cover retries"}]
WORKER = {"task_kind": "implementation", "complexity": "complex",
          "verification": "executable", "failure_cause": "none",
          "frame_confidence": "clear"}
RIGOUR = {"consequence": "consequential",
          "premise_uncertainty": "specific-checkable",
          "alternatives": "several-material",
          "constraint_coupling": "cross-module",
          "verification_gap": "incomplete-checks",
          "observed_failure_cause": "none", "required_output": "patch",
          "evidence_availability": "available"}
OPERATIONAL = {"context_tokens": 1000, "deadline_seconds": None,
               "prior_local_repairs": 0,
               "required_artefacts": ["payment.py", "report.json"],
               "deadline": None, "authorised_task_budget_usd": 12.0,
               "observed_at": "2026-09-27T00:00:00Z"}
TELEMETRY = {"provider_calls": 0, "model": None, "cost_usd": 0,
             "input_tokens": 0, "output_tokens": 0}


def interpretation(packet):
    fields = WORKER | RIGOUR
    return {"interpretation": {
        "schema_version": 1, "classifications": fields,
        "field_evidence": {key: ["e1", "e2"] for key in fields},
        "material_evidence": ["e1"]},
        "telemetry": TELEMETRY}


class PublicAssessmentTests(unittest.TestCase):
    def assess(self, actor=ACTOR, interpreter=interpretation):
        return public.assess_with(
            actor, issue="issue.md", source_paths=SOURCES,
            quote_requests=QUOTES, input_revision={"fixture": "public-v1"},
            interpreter=interpreter, operational=OPERATIONAL)

    def test_same_public_packet_feeds_both_production_validators(self):
        observed = []

        def capture(packet):
            observed.append(packet)
            return interpretation(packet)

        result = self.assess(interpreter=capture)
        self.assertEqual(1, len(observed))
        self.assertNotIn("family_id", str(observed[0]))
        self.assertNotIn("C03-D1", str(observed[0]))
        self.assertEqual("complex", result["worker"]["facts"]["complexity"])
        self.assertEqual("consequential", result["rigour"]["consequence"])
        self.assertEqual(0, result["telemetry"]["provider_calls"])
        self.assertEqual(64, len(result["assessment_sha256"]))
        control = controller_control.ControlDecision(
            "auto", "shipped-default", 0, result["rigour"]["task_revision"],
            "x3-public-fixture")
        decision = controller_policy.decide(
            result["rigour"], control, selected_cell="worker-sonnet-low",
            controller_profile="standard")
        self.assertEqual("controller", decision["recommended_action"])
        self.assertEqual("provisional", decision["qualification_status"])

    def test_hidden_paths_symlinks_and_stale_quotes_are_rejected(self):
        with self.assertRaises(public.PublicAssessmentError):
            public.collect(ACTOR, issue="issue.md",
                source_paths=["issue.md", "../../../../oracles/controller_x3/C03-D1.json"],
                quote_requests=QUOTES, input_revision={})
        with tempfile.TemporaryDirectory(prefix="x3-public-") as raw:
            actor = Path(raw) / "actor"
            shutil.copytree(ACTOR, actor)
            (actor / "linked.py").symlink_to(ACTOR / "public_check.py")
            with self.assertRaises(public.PublicAssessmentError):
                public.collect(actor, issue="issue.md",
                    source_paths=["issue.md", "linked.py"],
                    quote_requests=QUOTES, input_revision={})
            (actor / "issue.md").write_text("Changed issue\n", encoding="utf-8")
            with self.assertRaises(public.PublicAssessmentError):
                self.assess(actor)

    def test_hidden_interpretation_fields_and_unknown_cost_are_rejected(self):
        def hidden(packet):
            result = interpretation(packet)
            result["interpretation"]["family_id"] = "C03"
            return result

        with self.assertRaises(public.PublicAssessmentError):
            self.assess(interpreter=hidden)

        def unknown_cost(packet):
            result = interpretation(packet)
            result["telemetry"] = {"provider_calls": 1, "model": "unknown",
                                   "cost_usd": None, "input_tokens": 1,
                                   "output_tokens": 1}
            return result

        with self.assertRaises(public.PublicAssessmentError):
            self.assess(interpreter=unknown_cost)

    def test_packet_carries_capped_public_source_and_rechecks_citations(self):
        packet = public.collect(ACTOR, issue="issue.md", source_paths=SOURCES,
                                quote_requests=QUOTES,
                                input_revision={"fixture": "public-v1"})
        self.assertEqual(2, packet["schema_version"])
        sources = {row["path"]: row for row in packet["sources"]}
        self.assertEqual((ACTOR / "issue.md").read_text(encoding="utf-8"),
                         sources["issue.md"]["content"])
        self.assertIn("does not cover retries", sources["public_check.py"]["content"])

        forged = copy.deepcopy(packet)
        forged["sources"][0]["content"] = "substituted public issue\n"
        forged["packet_sha256"] = public._digest({
            key: value for key, value in forged.items() if key != "packet_sha256"})
        with self.assertRaises(public.PublicAssessmentError):
            public.assess(forged, interpretation(packet)["interpretation"],
                          OPERATIONAL, TELEMETRY)

        forged = copy.deepcopy(packet)
        forged["citations"][0]["quote"] = "a different conclusion"
        forged["packet_sha256"] = public._digest({
            key: value for key, value in forged.items() if key != "packet_sha256"})
        with self.assertRaises(public.PublicAssessmentError):
            public.assess(forged, interpretation(packet)["interpretation"],
                          OPERATIONAL, TELEMETRY)

        forged = copy.deepcopy(packet)
        forged["citations"][0]["source"] = ["issue.md"]
        with self.assertRaises(public.PublicAssessmentError):
            public.assess(forged, interpretation(packet)["interpretation"],
                          OPERATIONAL, TELEMETRY)

    def test_hidden_family_metadata_cannot_change_identical_public_assessment(self):
        with tempfile.TemporaryDirectory(prefix="x3-public-metadata-") as raw:
            project = Path(raw)
            actor = project / "actor"
            shutil.copytree(ACTOR, actor)
            metadata = project / "evaluation-metadata.json"
            metadata.write_text(json.dumps({"family_id": "C03", "split": "development"}),
                                encoding="utf-8")
            first = self.assess(actor)
            metadata.write_text(json.dumps({"family_id": "N04", "split": "reserved"}),
                                encoding="utf-8")
            second = self.assess(actor)
            self.assertEqual(first, second)

    def test_every_x3_actor_can_supply_public_code_without_hidden_metadata(self):
        fixtures = ROOT / "test" / "fixtures" / "controller_x3"
        actors = sorted(fixtures.glob("*/*/actor"))
        self.assertEqual(48, len(actors))
        for actor in actors:
            with self.subTest(actor=actor.parent.name):
                editable = json.loads((actor / "acceptance.json").read_text(
                    encoding="utf-8"))["editable_paths"]
                source = next(name for name in editable if name != "report.json")
                paths = list(dict.fromkeys(["issue.md", "app.py",
                                            "public_check.py", source]))
                heading = next(line for line in (actor / "issue.md").read_text(
                    encoding="utf-8").splitlines() if line.startswith("# "))
                public_lines = (actor / "public_check.py").read_text(
                    encoding="utf-8").splitlines()
                assertion = next(line for line in public_lines
                                 if line.lstrip().startswith("assert ")
                                 and public_lines.count(line) == 1)
                packet = public.collect(
                    actor, issue="issue.md", source_paths=paths,
                    quote_requests=[{"source": "issue.md", "quote": heading},
                                    {"source": "public_check.py", "quote": assertion}],
                    input_revision={"fixture": "x3-public-packet-v2"})
                public._validate_packet(packet)
                self.assertEqual(paths, [row["path"] for row in packet["sources"]])
                self.assertNotIn("oracle", packet)

if __name__ == "__main__":
    unittest.main()
