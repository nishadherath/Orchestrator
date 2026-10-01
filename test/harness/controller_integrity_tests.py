#!/usr/bin/env python3
"""Offline adversarial tests for Controller integrity-v1."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_integrity as integrity  # noqa: E402
import system_controller as controller  # noqa: E402
import validate_records  # noqa: E402


def external_acceptance(criteria: list[str] | None = None) -> dict:
    contract = {
        "version": 1,
        "kind": "rubric",
        "criteria": criteria or ["fix the duplicate"],
        "constraints": [],
        "required_outputs": ["result.txt"],
        "protected_paths": [],
        "command": [],
        "rubric": ["inspect the result"],
        "timeout_s": 30.0,
    }
    return {"contract": contract, "contract_digest": integrity.digest(contract)}


def candidate(ident: str, *, technique: str = "subtract", version: int = 2,
              introduced: list[dict] | None = None) -> dict:
    return {
        "id": ident,
        "technique": technique,
        "ledger_version": version,
        "premises_introduced": introduced or [],
    }


def critique(ident: str, verdict: str = "pass", *, derivable: bool = False) -> dict:
    return {"candidate_id": ident, "verdict": verdict, "derivable": derivable}


def selection(baseline: str, shortlist: list[str], *, version: int = 2,
              excluded: list[str] | None = None) -> dict:
    return {
        "baseline_id": baseline,
        "ledger_version": version,
        "shortlist": [
            {"candidate_id": ident, "rank": rank}
            for rank, ident in enumerate(shortlist, 1)
        ],
        "excluded": [
            {"candidate_id": ident, "reason": "rejected_by_critic"}
            for ident in (excluded or [])
        ],
    }


class ControllerIntegrityTests(unittest.TestCase):
    def test_false_stability_stops_before_generation_and_writes_gap_packet(self):
        scripted = controller._happy_path_script()
        fake = controller.FakeRoleRunner(
            scripted,
            classify_script={
                "controller-stability": {
                    "stable": False,
                    "reasoning": "a material premise remains unresolved",
                }
            },
        )
        with tempfile.TemporaryDirectory(prefix="controller-r1-stability-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="stability",
            )
            packet = json.loads((result.run_dir / "controller-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(result.outcome, "gap")
        self.assertNotIn(("generate", "generator"), fake.calls)
        self.assertEqual(packet["outcome"], "gap")
        self.assertEqual(packet["readiness"], "provisional-guidance")
        self.assertTrue(packet["verified_findings"])
        self.assertEqual(integrity.validate_evidence_packet(packet), [])

    def test_incomplete_critique_coverage_stops_before_selector(self):
        scripted = controller._happy_path_script()
        scripted[("critique", "critic")] = [[controller._canned()["critique"][0]]]
        fake = controller.FakeRoleRunner(scripted)
        with tempfile.TemporaryDirectory(prefix="controller-r1-coverage-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="coverage",
            )
        self.assertEqual(result.outcome, "gap")
        self.assertNotIn(("select", "selector"), fake.calls)
        self.assertIn("Critique coverage incomplete", result.record["next_cheapest_test"])

    def test_selector_exclusion_is_enforced(self):
        canned = controller._canned()
        rejected = copy.deepcopy(canned["selection"])
        rejected[0]["shortlist"] = []
        rejected[0]["excluded"].append({
            "candidate_id": "cand-002", "reason": "loses_to_b0",
        })
        scripted = controller._happy_path_script()
        scripted[("select", "selector")] = [rejected]
        fake = controller.FakeRoleRunner(scripted)
        with tempfile.TemporaryDirectory(prefix="controller-r1-selector-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="selector",
            )
        self.assertEqual(result.outcome, "gap")
        self.assertEqual(result.record["termination"], "no_improvement")

    def test_unverified_global_premise_yields_specific_partial_handoff(self):
        canned = controller._canned()
        measurement = copy.deepcopy(canned["measurement"])
        measurement[0].update(result="The source was unavailable", artefact="probe.log",
                              outcome="inconclusive")
        reframe = copy.deepcopy(canned["frame_v2"])
        reframe[0].update(text="Downstream behaviour remains unknown",
                          **{"class": "unverified"},
                          cheapest_verification="obtain downstream.py and inspect all callers")
        scripted = controller._happy_path_script()
        scripted[("verify", "verifier")] = [measurement]
        scripted[("frame", "framer")] = [canned["frame_v1"], reframe]
        fake = controller.FakeRoleRunner(scripted)
        with tempfile.TemporaryDirectory(prefix="controller-r1-partial-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; downstream source is unavailable.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="partial",
            )
            report = (result.run_dir / "REPORT.md").read_text(encoding="utf-8")
        self.assertEqual(result.outcome, "gap")
        self.assertIn("obtain downstream.py", result.record["next_cheapest_test"])
        self.assertIn("prem-003", result.record["unverified_load_bearing"])
        self.assertIn("Next cheapest test: Obtain evidence", report)
        self.assertNotIn("## Answer", report)

    def test_external_acceptance_is_frozen_across_reframe(self):
        canned = controller._canned()
        changed = copy.deepcopy(canned["frame_v2"])
        changed[-1]["acceptance_criteria"] = ["quietly change the target"]
        scripted = controller._happy_path_script()
        scripted[("frame", "framer")] = [canned["frame_v1"], changed, changed]
        fake = controller.FakeRoleRunner(scripted)
        with tempfile.TemporaryDirectory(prefix="controller-r1-acceptance-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="acceptance",
                acceptance=external_acceptance(),
            )
            packet = json.loads((result.run_dir / "controller-evidence.json").read_text(encoding="utf-8"))
            ledger = [json.loads(line) for line in
                      (result.run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(result.outcome, "gap")
        self.assertEqual(result.record["unmet_criteria"], ["fix the duplicate"])
        self.assertEqual(packet["acceptance_source"], "external")
        self.assertNotIn(("controller-stability", "controller"), fake.calls)
        self.assertEqual(fake.calls.count(("frame", "framer")), 3)
        self.assertEqual(
            [row["acceptance_criteria"] for row in ledger if row["type"] == "FrameRecord"],
            [["fix the duplicate"]],
        )

    def test_external_acceptance_echo_is_corrected_before_frame_commit(self):
        canned = controller._canned()
        changed = copy.deepcopy(canned["frame_v1"])
        for record in changed:
            if record["type"] == "FrameRecord":
                record["acceptance_criteria"] = ["fix the duplicate", "new unapproved criterion"]
        scripted = controller._happy_path_script()
        scripted[("frame", "framer")] = [changed, canned["frame_v1"], canned["frame_v2"]]
        fake = controller.FakeRoleRunner(scripted)
        with tempfile.TemporaryDirectory(prefix="controller-r1-acceptance-retry-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="acceptance-retry",
                acceptance=external_acceptance(),
            )
            ledger = [json.loads(line) for line in
                      (result.run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            rejected = (result.run_dir / "rejections.jsonl").read_text(encoding="utf-8")
        self.assertEqual(result.outcome, "solution")
        self.assertEqual(fake.calls.count(("frame", "framer")), 3)
        self.assertTrue(all(row["acceptance_criteria"] == ["fix the duplicate"]
                            for row in ledger if row["type"] == "FrameRecord"))
        self.assertIn("complete Framer batch was withheld", rejected)

    def test_external_acceptance_is_frozen_across_critique_reframe(self):
        canned = controller._canned()
        frame_v3 = copy.deepcopy(canned["frame_v2"])
        frame_v3[0].update(text="The Critic's premise was corrected", source="critique",
                           supersedes="prem-001", ledger_version=3, references=["prem-001"])
        frame_v3[1].update(ledger_version=3, references=["frame-002", "prem-004", "cand-001"])
        changed = copy.deepcopy(frame_v3)
        changed[1]["acceptance_criteria"] = ["an unapproved extra condition"]
        critique = copy.deepcopy(canned["critique"])
        critique[1]["falsified_premise_claims"] = [{"premise_id": "prem-001", "reason": "false"}]
        scripted = controller._happy_path_script()
        scripted[("frame", "framer")] = [canned["frame_v1"], canned["frame_v2"], changed, changed]
        scripted[("critique", "critic")] = [critique]
        fake = controller.FakeRoleRunner(scripted)
        with tempfile.TemporaryDirectory(prefix="controller-r1-critique-acceptance-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="critique-acceptance",
                acceptance=external_acceptance(),
            )
            ledger = [json.loads(line) for line in
                      (result.run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(result.outcome, "gap")
        self.assertEqual(result.record["unmet_criteria"], ["fix the duplicate"])
        self.assertEqual(fake.calls.count(("frame", "framer")), 4)
        self.assertEqual(
            [row["acceptance_criteria"] for row in ledger if row["type"] == "FrameRecord"],
            [["fix the duplicate"], ["fix the duplicate"]],
        )

    def test_external_acceptance_can_produce_verified_ready_guidance(self):
        fake = controller.FakeRoleRunner(controller._happy_path_script())
        with tempfile.TemporaryDirectory(prefix="controller-r1-ready-") as folder:
            result = controller.run_quick(
                "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
                Path(folder), 5.0, 30, lambda _remaining: fake, run_id="ready",
                acceptance=external_acceptance(),
            )
            packet = json.loads((result.run_dir / "controller-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(result.outcome, "solution")
        self.assertEqual(packet["readiness"], "verified-ready")
        self.assertEqual(packet["acceptance_source"], "external")
        self.assertEqual({row["path"] for row in packet["artefacts"]}, {"REPORT.md", "ledger.jsonl"})
        self.assertEqual(integrity.validate_evidence_packet(packet), [])

    def test_eligibility_rejects_unverified_introduced_premise(self):
        baseline = candidate("cand-001", technique="b0", version=1)
        proposed = candidate(
            "cand-002",
            introduced=[{"text": "the cache is coherent", "class": "unverified"}],
        )
        winner, detail = integrity.select_candidate(
            [baseline, proposed],
            [critique("cand-001", "return"), critique("cand-002")],
            selection("cand-001", ["cand-002"], excluded=["cand-001"]),
            {"ledger_version": 2, "b0_candidate_id": "cand-001"},
            "cand-001", [],
        )
        self.assertIsNone(winner)
        self.assertIn("unverified-introduced-premise", detail["reasons"]["cand-002"])

    def test_stale_selection_and_stale_baseline_are_rejected(self):
        baseline = candidate("cand-001", technique="b0", version=1)
        stale_selection = selection("cand-001", [], version=1)
        winner, detail = integrity.select_candidate(
            [baseline], [critique("cand-001")], stale_selection,
            {"ledger_version": 2, "b0_candidate_id": "cand-999"},
            "cand-001", [],
        )
        self.assertIsNone(winner)
        self.assertFalse(detail["selection_ledger_current"])
        self.assertIn("stale-baseline", detail["reasons"]["cand-001"])

    def test_current_passing_baseline_is_a_valid_fallback(self):
        baseline = candidate("cand-001", technique="b0", version=1)
        winner, detail = integrity.select_candidate(
            [baseline], [critique("cand-001")], selection("cand-001", []),
            {"ledger_version": 2, "b0_candidate_id": "cand-001"},
            "cand-001", [],
        )
        self.assertEqual(winner, baseline)
        self.assertEqual(detail["eligible_ids"], ["cand-001"])

    def test_contract_and_packet_digests_reject_tampering(self):
        acceptance = external_acceptance()
        acceptance["contract"]["criteria"] = ["mutated"]
        with self.assertRaisesRegex(ValueError, "digest"):
            integrity.freeze_acceptance(acceptance)

        frozen = integrity.freeze_provisional(["criterion"], [])
        packet = integrity.build_evidence_packet(
            problem_text="problem", project_identity="project", acceptance=frozen,
            input_revision={"head": "abc", "diff_sha256": "d", "status_sha256": "s"},
            outcome="gap", readiness="provisional-guidance",
            premises=[], candidates=[], critiques=[],
            record={"next_cheapest_test": "inspect"},
            artefacts=[{"path": "REPORT.md", "sha256": "a" * 64, "size": 1}],
            accounting={"known_spend_usd": 0.0, "reserved_usd": 0.0,
                        "accounting_complete": True},
        )
        packet["safe_next_action"] = "tampered"
        self.assertIn("packet digest does not match content", integrity.validate_evidence_packet(packet))

    def test_evidence_packet_schema_and_path_boundary(self):
        frozen = integrity.freeze_provisional(["criterion"], [])
        packet = integrity.build_evidence_packet(
            problem_text="problem", project_identity="project", acceptance=frozen,
            input_revision={"head": "abc", "diff_sha256": "d", "status_sha256": "s"},
            outcome="gap", readiness="blocked", premises=[], candidates=[], critiques=[],
            record={"next_cheapest_test": "inspect"},
            artefacts=[{"path": "../secret", "sha256": "a" * 64, "size": 1}],
            accounting={"known_spend_usd": 0.0, "reserved_usd": 0.0,
                        "accounting_complete": True},
        )
        self.assertIn(
            "artefacts need safe relative paths and sha256",
            integrity.validate_evidence_packet(packet),
        )
        schema = validate_records.load_schemas()["ControllerEvidencePacket"]
        errors: list[str] = []
        validate_records.validate_node(packet, schema, "$", errors)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
