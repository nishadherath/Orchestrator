#!/usr/bin/env python3
"""Pure integrity rules for Controller quick-mode decisions and handoffs.

This module deliberately performs no model calls and writes no files. The
state machine supplies frozen records; these functions decide whether a frame
or candidate may advance and build the compact evidence packet persisted by
``system_controller.py``.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

INTEGRITY_V1 = "integrity-v1"
LEGACY_QUICK_V0 = "legacy-quick-v0"
POLICIES = (INTEGRITY_V1, LEGACY_QUICK_V0)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def freeze_acceptance(acceptance: dict | None) -> dict | None:
    """Copy and verify an acceptance.py value before any Controller role runs."""
    if acceptance is None:
        return None
    contract = acceptance.get("contract")
    contract_digest = acceptance.get("contract_digest")
    if not isinstance(contract, dict) or digest(contract) != contract_digest:
        raise ValueError("acceptance contract digest does not match its content")
    criteria = contract.get("criteria")
    constraints = contract.get("constraints", [])
    if (not isinstance(criteria, list) or not criteria
            or not all(isinstance(item, str) and item.strip() for item in criteria)):
        raise ValueError("acceptance contract needs non-empty criteria")
    if not isinstance(constraints, list) or not all(isinstance(item, str) for item in constraints):
        raise ValueError("acceptance contract constraints must be strings")
    return {
        "source": "external",
        "contract_digest": contract_digest,
        "criteria": list(criteria),
        "constraints": list(constraints),
    }


def freeze_provisional(criteria: list[str], constraints: list[str]) -> dict:
    """Freeze a first-frame fallback while labelling it as non-external."""
    value = {
        "source": "framer-provisional",
        "criteria": list(criteria),
        "constraints": list(constraints),
    }
    value["contract_digest"] = digest(value)
    return value


def frame_matches_acceptance(frame: dict, acceptance: dict) -> bool:
    return frame.get("acceptance_criteria") == acceptance["criteria"]


def critique_coverage(candidates: list[dict], critiques: list[dict]) -> dict[str, list[dict]]:
    """Return critiques by candidate; callers require exactly one per candidate."""
    coverage = {candidate["id"]: [] for candidate in candidates}
    for critique in critiques:
        candidate_id = critique.get("candidate_id")
        if candidate_id in coverage:
            coverage[candidate_id].append(critique)
    return coverage


def select_candidate(candidates: list[dict], critiques: list[dict], selection: dict,
                     frame: dict, baseline_id: str, premises: list[dict]) -> tuple[dict | None, dict]:
    """Apply deterministic eligibility before honouring Selector rank order."""
    by_id = {candidate["id"]: candidate for candidate in candidates}
    coverage = critique_coverage(candidates, critiques)
    excluded_by_selector = {row["candidate_id"] for row in selection.get("excluded", [])}
    global_unverified = [
        premise["id"] for premise in premises
        if premise.get("class") == "unverified" and premise.get("load_bearing")
    ]
    reasons: dict[str, list[str]] = {}
    eligible: set[str] = set()
    for candidate in candidates:
        ident = candidate["id"]
        why: list[str] = []
        if ident == baseline_id:
            if frame.get("b0_candidate_id") != ident:
                why.append("stale-baseline")
        elif candidate.get("ledger_version") != frame.get("ledger_version"):
            why.append("stale-ledger")
        candidate_critiques = coverage.get(ident, [])
        if len(candidate_critiques) != 1:
            why.append("critique-coverage")
        else:
            critique = candidate_critiques[0]
            if critique.get("verdict") != "pass":
                why.append("critic-verdict")
            if critique.get("derivable"):
                why.append("derivable")
        if any(item.get("class") == "unverified"
               for item in candidate.get("premises_introduced", [])):
            why.append("unverified-introduced-premise")
        if global_unverified:
            why.append("unverified-load-bearing-premise")
        if ident in excluded_by_selector:
            why.append("selector-excluded")
        reasons[ident] = why
        if not why:
            eligible.add(ident)

    order = [row["candidate_id"] for row in sorted(
        selection.get("shortlist", []), key=lambda row: row["rank"]
    )]
    if selection.get("baseline_id") != baseline_id:
        order = []
    if baseline_id not in excluded_by_selector:
        order.append(baseline_id)
    order = list(dict.fromkeys(order))
    if selection.get("ledger_version") != frame.get("ledger_version"):
        return None, {
        "eligible_ids": [],
        "reasons": {**reasons, "selection": ["stale-ledger"]},
        "global_unverified_load_bearing": global_unverified,
        "selection_ledger_current": False,
        }
    winner = next((by_id[ident] for ident in order if ident in eligible and ident in by_id), None)
    return winner, {
        "eligible_ids": sorted(eligible),
        "reasons": reasons,
        "global_unverified_load_bearing": global_unverified,
        "selection_ledger_current": True,
    }


def build_evidence_packet(*, problem_text: str, project_identity: str,
                          input_revision: dict,
                          acceptance: dict, outcome: str, readiness: str,
                          premises: list[dict], candidates: list[dict],
                          critiques: list[dict], record: dict,
                          artefacts: list[dict], accounting: dict) -> dict:
    """Build the compact, transcript-free packet a later worker may consume."""
    verified = [{
        "premise_id": premise["id"],
        "text": premise["text"],
        "source": premise.get("source", ""),
        "confidence": premise.get("confidence"),
    } for premise in premises if premise.get("class") == "verified"]
    rejected = [{
        "candidate_id": critique["candidate_id"],
        "verdict": critique["verdict"],
        "failure_modes": list(critique.get("failure_modes", [])),
    } for critique in critiques if critique.get("verdict") != "pass"]
    uncertainties = [{
        "premise_id": premise["id"],
        "text": premise["text"],
        "next_test": premise.get("cheapest_verification", "none"),
    } for premise in premises if premise.get("class") == "unverified"]
    input_identity = {"project": project_identity, "revision": input_revision}
    packet = {
        "packet_version": 1,
        "task_revision": digest({"problem": problem_text, "input": input_identity}),
        "task_digest": digest(problem_text),
        "acceptance_contract_digest": acceptance["contract_digest"],
        "acceptance_source": acceptance["source"],
        "input_snapshot_digest": digest(input_identity),
        "outcome": outcome,
        "readiness": readiness,
        "premise_ids": [premise["id"] for premise in premises],
        "candidate_ids": [candidate["id"] for candidate in candidates],
        "verified_findings": verified,
        "rejected_hypotheses": rejected,
        "remaining_uncertainties": uncertainties,
        "safe_next_action": record.get("next_cheapest_test", "implement then verify")[:300],
        "operator_question": None,
        "artefacts": artefacts,
        "accounting": accounting,
    }
    packet["packet_digest"] = digest(packet)
    return packet


def validate_evidence_packet(packet: dict) -> list[str]:
    """Validate cross-field properties that the compact JSON schema cannot express."""
    errors: list[str] = []
    required = {
        "packet_version", "task_revision", "task_digest", "acceptance_contract_digest",
        "acceptance_source", "input_snapshot_digest", "outcome", "readiness", "premise_ids",
        "candidate_ids", "verified_findings", "rejected_hypotheses", "remaining_uncertainties",
        "safe_next_action", "operator_question", "artefacts", "accounting", "packet_digest",
    }
    if set(packet) != required:
        errors.append("packet fields do not match version 1")
    if packet.get("outcome") == "gap" and packet.get("readiness") == "verified-ready":
        errors.append("a gap cannot claim verified-ready")
    if packet.get("acceptance_source") != "external" and packet.get("readiness") == "verified-ready":
        errors.append("non-external acceptance cannot claim verified-ready")
    for artefact in packet.get("artefacts", []):
        path = artefact.get("path", "")
        if not path or PathLike.is_absolute_or_escaping(path) or not artefact.get("sha256"):
            errors.append("artefacts need safe relative paths and sha256")
    expected = dict(packet)
    recorded = expected.pop("packet_digest", None)
    if digest(expected) != recorded:
        errors.append("packet digest does not match content")
    return errors


class PathLike:
    """Small path check kept independent of host filesystem resolution."""

    @staticmethod
    def is_absolute_or_escaping(value: str) -> bool:
        normal = value.replace("\\", "/")
        return normal.startswith("/") or ":" in normal.split("/", 1)[0] or ".." in normal.split("/")
