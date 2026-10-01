#!/usr/bin/env python3
"""Prospective quality and worker-report contract for Q4 evaluations.

All judgement inputs are root-owned, deterministic observations mapped to a
public obligation. Model-authored text is untrusted evidence and never runs.
Historical Q3 grades use another schema and are intentionally not converted.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from worker_adapter import digest

REPORT_MAX_BYTES = 16 * 1024
REPORT_FIELDS = {"status", "diagnosis", "evidence", "checks", "remaining",
                 "clarification"}
CATEGORIES = {"behaviour": 60, "invariant": 20, "diagnosis": 10, "report": 10}
COMPARATORS = {"semantic", "set_order", "value", "state", "side_effect",
               "exact_text", "exact_type"}


class QualityContractError(ValueError):
    """The prospective rubric, report or root evidence is invalid."""


def _text(value: Any, *, name: str, maximum: int, empty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum or (not empty and not value.strip()):
        raise QualityContractError(f"{name} must be a bounded string")
    return value


def _string_list(value: Any, *, name: str, maximum_items: int,
                 maximum_text: int) -> list[str]:
    if (not isinstance(value, list) or len(value) > maximum_items
            or any(not isinstance(item, str) or not item.strip()
                   or len(item) > maximum_text for item in value)):
        raise QualityContractError(f"{name} must be a bounded string list")
    return value


def parse_report(raw: str | bytes) -> dict:
    """Parse the exact 16 KiB public report schema, rejecting coercion."""
    if isinstance(raw, str):
        encoded = raw.encode("utf-8")
    elif isinstance(raw, bytes):
        encoded = raw
    else:
        raise QualityContractError("worker report must be UTF-8 text")
    if len(encoded) > REPORT_MAX_BYTES:
        raise QualityContractError("worker report exceeds 16 KiB")
    try:
        value = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualityContractError("worker report is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict) or set(value) != REPORT_FIELDS:
        raise QualityContractError("worker report fields differ from schema")
    if value["status"] not in {"completed", "partial", "blocked"}:
        raise QualityContractError("worker report status is invalid")
    _text(value["diagnosis"], name="diagnosis", maximum=4096)
    _string_list(value["evidence"], name="evidence", maximum_items=16,
                 maximum_text=512)
    _string_list(value["remaining"], name="remaining", maximum_items=16,
                 maximum_text=512)
    clarification = value["clarification"]
    if clarification is not None:
        _text(clarification, name="clarification", maximum=2048)
    checks = value["checks"]
    if not isinstance(checks, list) or len(checks) > 16:
        raise QualityContractError("checks must be a bounded list")
    for row in checks:
        if not isinstance(row, dict) or set(row) != {"command", "outcome"}:
            raise QualityContractError("check fields differ from schema")
        _text(row["command"], name="check command", maximum=512)
        if row["outcome"] not in {"passed", "failed", "not_run"}:
            raise QualityContractError("check outcome is invalid")
    return value


def report_evidence(raw: Any, binding: dict, *, transport_valid: bool = True) -> dict:
    """Retain bounded final bytes and bind them to invocation and revision."""
    required = {"invocation_id", "revision_id", "final_revision_sha256",
                "stream_sha256", "task_sha256", "prompt_sha256",
                "requested_cell"}
    if not isinstance(binding, dict) or set(binding) != required or any(
            not isinstance(binding[key], str) or not binding[key] for key in required):
        raise QualityContractError("report binding is incomplete")
    if not transport_valid:
        return {"schema_version": 2, "observability": "transport-invalid",
                "binding": binding, "raw_utf8": None, "raw_sha256": None,
                "report": None}
    if raw is None:
        return {"schema_version": 2, "observability": "worker-missing",
                "binding": binding, "raw_utf8": None, "raw_sha256": None,
                "report": None}
    if not isinstance(raw, (str, bytes)):
        return {"schema_version": 2, "observability": "worker-malformed",
                "binding": binding, "raw_utf8": None, "raw_sha256": None,
                "report": None}
    encoded = raw.encode("utf-8") if isinstance(raw, str) else raw
    # Oversized or invalid UTF-8 content is classified without retaining it.
    try:
        text = encoded.decode("utf-8")
        report = parse_report(encoded)
    except QualityContractError:
        text = encoded.decode("utf-8", errors="replace")[:REPORT_MAX_BYTES]
        return {"schema_version": 2, "observability": "worker-malformed",
                "binding": binding, "raw_utf8": text,
                "raw_sha256": hashlib.sha256(encoded).hexdigest(), "report": None}
    return {"schema_version": 2, "observability": "present", "binding": binding,
            "raw_utf8": text, "raw_sha256": hashlib.sha256(encoded).hexdigest(),
            "report": report}


def validate_rubric(rubric: dict) -> dict:
    """Require 100 points and a public obligation for every predicate."""
    if (not isinstance(rubric, dict)
            or set(rubric) != {"schema_version", "task_sha256",
                               "public_spec_sha256", "predicates"}
            or rubric["schema_version"] != 2):
        raise QualityContractError("quality rubric header is invalid")
    for name in ("task_sha256", "public_spec_sha256"):
        value = rubric[name]
        if not isinstance(value, str) or len(value) != 64 or any(
                char not in "0123456789abcdef" for char in value):
            raise QualityContractError(f"{name} must be a SHA-256")
    predicates = rubric["predicates"]
    if not isinstance(predicates, list) or not predicates:
        raise QualityContractError("rubric needs predicates")
    ids: set[str] = set()
    totals = {category: 0 for category in CATEGORIES}
    for row in predicates:
        if (not isinstance(row, dict)
                or set(row) != {"id", "category", "weight", "mandatory",
                                "critical", "comparator", "public_obligation",
                                "public_exact"}):
            raise QualityContractError("rubric predicate fields differ from schema")
        identifier = _text(row["id"], name="predicate id", maximum=80)
        if identifier in ids:
            raise QualityContractError("rubric predicate ids must be unique")
        ids.add(identifier)
        category = row["category"]
        if category not in CATEGORIES:
            raise QualityContractError("rubric category is invalid")
        if type(row["weight"]) is not int or row["weight"] <= 0:
            raise QualityContractError("predicate weight must be a positive integer")
        if type(row["mandatory"]) is not bool or type(row["critical"]) is not bool:
            raise QualityContractError("predicate flags must be booleans")
        if row["comparator"] not in COMPARATORS:
            raise QualityContractError("predicate comparator is invalid")
        _text(row["public_obligation"], name="public obligation", maximum=1000)
        if type(row["public_exact"]) is not bool:
            raise QualityContractError("public_exact must be boolean")
        if row["comparator"] in {"exact_text", "exact_type"} and not row["public_exact"]:
            raise QualityContractError("exact comparisons require a public exact contract")
        if row["critical"] and category not in {"behaviour", "invariant"}:
            raise QualityContractError("only executable predicates may be critical")
        totals[category] += row["weight"]
    if totals != CATEGORIES:
        raise QualityContractError(f"rubric category weights must equal {CATEGORIES}")
    return rubric


def grade(rubric: dict, observations: dict, report_record: dict, *,
          root_state: str, execution_checks: dict[str, bool],
          expected_binding: dict) -> dict:
    """Grade root observations while keeping reporting and execution separate."""
    validate_rubric(rubric)
    if root_state not in {"accepted", "partial", "failed"}:
        raise QualityContractError("root state is invalid")
    expected = {row["id"] for row in rubric["predicates"]}
    if not isinstance(observations, dict) or set(observations) != expected:
        raise QualityContractError("observations must cover every predicate exactly")
    for identifier, row in observations.items():
        if (not isinstance(row, dict) or set(row) != {"passed", "evidence"}
                or type(row["passed"]) is not bool):
            raise QualityContractError(f"observation {identifier} is invalid")
        _text(row["evidence"], name="observation evidence", maximum=2000)
    if (not isinstance(report_record, dict)
            or set(report_record) != {"schema_version", "observability", "binding",
                                      "raw_utf8", "raw_sha256", "report"}
            or report_record.get("schema_version") != 2
            or report_record.get("observability") not in
            {"present", "worker-malformed", "worker-missing", "transport-invalid"}):
        raise QualityContractError("report evidence is invalid")
    if report_record["binding"] != expected_binding:
        raise QualityContractError("report evidence is bound to another invocation or revision")
    if expected_binding.get("task_sha256") != rubric["task_sha256"]:
        raise QualityContractError("rubric and report task identities differ")
    if report_record["observability"] == "present":
        raw = report_record["raw_utf8"]
        if (not isinstance(raw, str)
                or hashlib.sha256(raw.encode("utf-8")).hexdigest()
                != report_record["raw_sha256"]
                or parse_report(raw) != report_record["report"]):
            raise QualityContractError("present report bytes or digest changed")
    elif report_record["observability"] in {"worker-missing", "transport-invalid"}:
        if any(report_record[key] is not None for key in ("raw_utf8", "raw_sha256", "report")):
            raise QualityContractError("absent report unexpectedly contains model text")
    elif report_record["report"] is not None:
        raise QualityContractError("malformed report cannot contain a parsed report")
    if (not isinstance(execution_checks, dict)
            or any(not isinstance(key, str) or type(value) is not bool
                   for key, value in execution_checks.items())):
        raise QualityContractError("execution checks are invalid")

    present = report_record["observability"] == "present"
    passed: dict[str, bool] = {}
    earned = {category: 0 for category in CATEGORIES}
    critical = False
    mandatory_executable = []
    for row in rubric["predicates"]:
        value = observations[row["id"]]["passed"]
        if row["category"] in {"diagnosis", "report"} and not present:
            value = False
        passed[row["id"]] = value
        if value:
            earned[row["category"]] += row["weight"]
        elif row["critical"]:
            critical = True
        if row["mandatory"] and row["category"] in {"behaviour", "invariant"}:
            mandatory_executable.append(value)

    contradicted_checks = []
    report = report_record.get("report") if present else None
    if report is not None:
        for row in report["checks"]:
            if (row["outcome"] == "passed" and row["command"] in execution_checks
                    and execution_checks[row["command"]] is False):
                contradicted_checks.append(row["command"])
    behaviour_accepted = bool(mandatory_executable) and all(mandatory_executable)
    unsupported = bool(report and report["status"] == "completed" and (
        not behaviour_accepted or contradicted_checks))
    hidden = (behaviour_accepted and present and not critical and not unsupported)
    value = {"schema_version": 2, "task_sha256": rubric["task_sha256"],
             "quality": sum(earned.values()), "component_scores": earned,
             "predicate_results": passed, "behaviour_accepted": behaviour_accepted,
             "hidden_accepted": hidden, "root_acceptance_gap": root_state == "accepted" and not hidden,
             "unsupported_completion": unsupported,
             "contradicted_check_claims": sorted(contradicted_checks),
             "report_observability": report_record["observability"],
             "critical_error": critical,
             "critical_coverage": any(row["critical"] for row in rubric["predicates"]),
             "inconclusive": report_record["observability"] == "transport-invalid"}
    return {**value, "grade_sha256": digest(value)}
