#!/usr/bin/env python3
"""Q4U offline public-check assessment and non-dispatching policy table.

This experiment consumes only caller-supplied public issue/check text. It
does not read a repository, grade an outcome, contact a provider or alter B0.
The cited lines prove provenance, not semantic adequacy: a human must review
whether an assertion really checks the cited requirement before a paid screen.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


VERSION = "q4u-coverage-v1"
LOW = "worker-sonnet-low"
MEDIUM = "worker-sonnet-medium"
POLICIES = ("b0", "cross_component_medium", "coverage_repair")
REPAIR_TAIL = (LOW, "worker-opus-high")


class CoverageError(ValueError):
    """Public assessment or policy input is incomplete or unsupported."""


def _exact(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise CoverageError(f"{label} fields differ")


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _public_files(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise CoverageError(f"{label} needs public files")
    for path, content in value.items():
        if (not isinstance(path, str) or not path or path.startswith("/")
                or "\\" in path or any(part in {"", ".", ".."}
                                      for part in path.split("/"))
                or any(part.lower() in {"hidden", "oracle", "oracles", "reference",
                                        "references", "results"}
                       for part in path.split("/"))
                or not isinstance(content, str)):
            raise CoverageError(f"{label} contains a non-public path or invalid text")
    return value


def _citation(value: Any, files: dict[str, str], label: str) -> None:
    _exact(value, {"path", "line", "text", "file_sha256"}, label)
    path, line = value["path"], value["line"]
    if path not in files or type(line) is not int:
        raise CoverageError(f"{label} is not in the public inventory")
    lines = files[path].splitlines()
    if (line < 1 or line > len(lines) or value["text"] != lines[line - 1]
            or value["file_sha256"] != hashlib.sha256(
                files[path].encode("utf-8")).hexdigest()):
        raise CoverageError(f"{label} bytes or line differ")


def assess(facts: dict, *, issue_files: dict[str, str],
           check_files: dict[str, str]) -> dict:
    """Validate cited public facts; return a versioned aggregate assessment.

    A `direct` label must cite a public check and is still a reviewable human
    claim. `partial` cites a check and explains the uncovered requirement.
    `unknown` abstains, including when check relevance cannot be established.
    """
    issues = _public_files(issue_files, "issue inventory")
    checks = _public_files(check_files, "check inventory")
    if set(issues) & set(checks):
        raise CoverageError("issue and check inventories overlap")
    _exact(facts, {"task_kind", "cross_component", "change_required", "criteria"},
           "facts")
    if facts["task_kind"] not in {"implementation", "investigation"}:
        raise CoverageError("task kind is invalid")
    if type(facts["cross_component"]) is not bool or type(facts["change_required"]) is not bool:
        raise CoverageError("routing flags must be booleans")
    if facts["task_kind"] == "investigation" and facts["change_required"]:
        raise CoverageError("investigation cannot require an implementation edit")
    criteria = facts["criteria"]
    if not isinstance(criteria, list) or not criteria or len(criteria) > 16:
        raise CoverageError("one to sixteen public criteria are required")
    seen: set[str] = set()
    for row in criteria:
        _exact(row, {"id", "coverage", "issue_citation", "check_citations", "gap"},
               "criterion")
        name = row["id"]
        if not isinstance(name, str) or not name or name in seen:
            raise CoverageError("criterion id is empty or duplicated")
        seen.add(name)
        if row["coverage"] not in {"direct", "partial", "unknown"}:
            raise CoverageError("coverage value is invalid")
        _citation(row["issue_citation"], issues, "issue citation")
        refs = row["check_citations"]
        if not isinstance(refs, list) or len(refs) > 8:
            raise CoverageError("check citations are invalid")
        for ref in refs:
            _citation(ref, checks, "check citation")
        gap = row["gap"]
        if not isinstance(gap, str) or len(gap) > 500:
            raise CoverageError("coverage gap is invalid")
        if row["coverage"] == "direct" and (not refs or gap):
            raise CoverageError("direct coverage needs a check and no gap")
        if row["coverage"] == "partial" and (not refs or not gap.strip()):
            raise CoverageError("partial coverage needs a check and gap")
        if row["coverage"] == "unknown" and not gap.strip():
            raise CoverageError("unknown coverage needs a reason")
    values = {row["coverage"] for row in criteria}
    coverage = ("unknown" if "unknown" in values else
                "partial" if "partial" in values else "direct")
    value = {"schema_version": 1, "policy": VERSION,
             "verification_coverage": coverage, "facts": facts,
             "public_file_sha256": {path: hashlib.sha256(content.encode("utf-8")).hexdigest()
                                    for path, content in sorted({**issues, **checks}.items())}}
    return {**value, "assessment_sha256": _digest(value)}


def decision(assessment: dict, *, policy: str, phase: str,
             low_outcome: str | None, supported_cells: set[str],
             remaining_usd: float, call_ceiling_usd: float,
             budget_enforced: bool) -> dict:
    """Return one prospective action; never dispatch or claim measured quality.

    `after_low` is a real future continuation state, not a counterfactual
    constructed from independent Q4T low and medium arms. Every call consumes
    its full admission ceiling until actual settled cost is known.
    """
    if (not isinstance(assessment, dict) or assessment.get("policy") != VERSION
            or assessment.get("schema_version") != 1 or policy not in POLICIES
            or phase not in {"initial", "after_low"}
            or low_outcome not in ({None} if phase == "initial" else
                                   {"accepted", "no_change", "verification_failed", "blocked"})
            or not isinstance(supported_cells, set)
            or any(not isinstance(cell, str) for cell in supported_cells)
            or type(budget_enforced) is not bool):
        raise CoverageError("policy state is invalid")
    _exact(assessment, {"schema_version", "policy", "verification_coverage",
                        "facts", "public_file_sha256", "assessment_sha256"},
           "assessment")
    try:
        intact = assessment["assessment_sha256"] == _digest({
            key: value for key, value in assessment.items() if key != "assessment_sha256"})
    except (TypeError, ValueError):
        intact = False
    if not intact:
        raise CoverageError("assessment bytes changed after validation")
    facts = assessment.get("facts")
    if (not isinstance(facts, dict) or facts.get("task_kind") not in
            {"implementation", "investigation"}
            or type(facts.get("cross_component")) is not bool
            or type(facts.get("change_required")) is not bool
            or assessment.get("verification_coverage") not in
            {"direct", "partial", "unknown"}):
        raise CoverageError("assessment facts are invalid")
    for amount in (remaining_usd, call_ceiling_usd):
        if type(amount) not in (int, float) or not 0 <= amount < float("inf"):
            raise CoverageError("finite non-negative cost bounds are required")
    if call_ceiling_usd == 0:
        raise CoverageError("call ceiling must be positive")
    action, reason = "stop", None
    if phase == "initial":
        action = MEDIUM if policy == "cross_component_medium" and facts["cross_component"] else LOW
        reason = "cross_component" if action == MEDIUM else "baseline_first"
    elif low_outcome == "accepted":
        reason = "accepted_without_hidden_inference"
    elif low_outcome == "blocked":
        reason = "review_blocked_evidence"
    elif (policy == "coverage_repair" and facts["task_kind"] == "implementation"
          and facts["change_required"] and
          assessment["verification_coverage"] == "partial"):
        action, reason = MEDIUM, "partial_public_check_after_low_failure"
    else:
        action, reason = REPAIR_TAIL[0], "baseline_repair"
    if action != "stop" and action not in supported_cells:
        if action == MEDIUM and LOW in supported_cells:
            action, reason = LOW, "abstain_medium_unavailable"
        else:
            action, reason = "stop", "host_unsupported"
    if action != "stop" and not budget_enforced:
        action, reason = "stop", "budget_not_enforced"
    if action != "stop" and remaining_usd < call_ceiling_usd:
        action, reason = "stop", "call_ceiling_unfunded"
    return {"schema_version": 1, "policy": policy, "phase": phase,
            "action": action, "reason": reason,
            "maximum_new_calls": 0 if action == "stop" else 1,
            "reserved_usd": 0 if action == "stop" else call_ceiling_usd,
            "quality_status": "unmeasured", "dispatch": False}
