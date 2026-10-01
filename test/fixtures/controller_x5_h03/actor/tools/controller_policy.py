#!/usr/bin/env python3
"""Pure rigour assessment and Controller-routing policy for R4.

The module validates operator/repository evidence, computes the candidate
``rigour-auto-v1`` recommendation, then applies an already-resolved R3 control
snapshot.  It performs no file writes and no model or worker dispatch.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import controller_control
import model_registry


POLICY_ID = "rigour-auto-v1"
ASSESSMENT_VERSION = 1
DECISION_VERSION = 1
CONTROLLER_INVOCATION_LIMIT = 1
DEFAULT_CONTROLLER_ALLOWANCE_USD = 4.0

CONSEQUENCE = ("contained", "recoverable", "consequential", "irreversible")
PREMISE_UNCERTAINTY = ("none", "specific-checkable", "contradictory", "unavailable")
ALTERNATIVES = ("one-established", "several-material", "unknown")
COUPLING = ("local", "cross-module", "cross-system")
VERIFICATION_GAP = ("strong-existing-checks", "incomplete-checks", "rubric-only")
FAILURE_CAUSE = ("none", "implementation", "premise-conflict", "no-new-evidence",
                 "infrastructure", "context-overflow")
REQUIRED_OUTPUT = ("patch", "decision", "investigation", "clarification")
EVIDENCE_AVAILABILITY = ("available", "partial", "unavailable")
PROVENANCE = ("operator-fact", "repository-artefact", "model-inference")
HEX64 = set("0123456789abcdef")

ASSESSMENT_FIELDS = {
    "assessment_version", "task_revision", "consequence", "premise_uncertainty",
    "alternatives", "constraint_coupling", "verification_gap", "observed_failure_cause",
    "required_output", "evidence_availability", "deadline", "authorised_task_budget_usd",
    "evidence",
}


class PolicyError(ValueError):
    """Invalid or incomplete policy input."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def derive_task_revision(problem_text: str, project: Path, input_revision: dict) -> str:
    """Match ControllerEvidencePacket's task-revision construction exactly."""
    identity = {"project": digest(str(project.resolve())), "revision": input_revision}
    return digest({"problem": problem_text, "input": identity})


def _enum(value: object, choices: tuple[str, ...], name: str) -> None:
    if value not in choices:
        raise PolicyError(f"{name} must be one of {choices}")


def validate_assessment(value: object) -> dict:
    """Validate a complete v1 assessment; unknown evidence is never false."""
    if not isinstance(value, dict) or set(value) != ASSESSMENT_FIELDS:
        raise PolicyError("RigourAssessment fields do not match version 1")
    if value["assessment_version"] != ASSESSMENT_VERSION:
        raise PolicyError("assessment_version must be 1")
    revision = value["task_revision"]
    if not isinstance(revision, str) or len(revision) != 64 or any(c not in HEX64 for c in revision):
        raise PolicyError("task_revision must be a lowercase SHA-256 digest")
    for field, choices in (
        ("consequence", CONSEQUENCE), ("premise_uncertainty", PREMISE_UNCERTAINTY),
        ("alternatives", ALTERNATIVES), ("constraint_coupling", COUPLING),
        ("verification_gap", VERIFICATION_GAP), ("observed_failure_cause", FAILURE_CAUSE),
        ("required_output", REQUIRED_OUTPUT), ("evidence_availability", EVIDENCE_AVAILABILITY),
    ):
        _enum(value[field], choices, field)
    deadline = value["deadline"]
    if deadline is not None and (not isinstance(deadline, str) or not deadline.strip() or len(deadline) > 100):
        raise PolicyError("deadline must be null or a non-empty string no longer than 100 characters")
    budget = value["authorised_task_budget_usd"]
    if budget is not None and (isinstance(budget, bool) or not isinstance(budget, (int, float))
                               or not math.isfinite(budget) or budget < 0):
        raise PolicyError("authorised_task_budget_usd must be null or a finite non-negative number")
    evidence = value["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 32:
        raise PolicyError("evidence must be a list of at most 32 records")
    seen: set[str] = set()
    for index, row in enumerate(evidence):
        required = {"id", "provenance", "observed_at", "scope", "claim", "material"}
        if not isinstance(row, dict) or set(row) != required:
            raise PolicyError(f"evidence[{index}] fields are invalid")
        ident = row["id"]
        if not isinstance(ident, str) or not ident or len(ident) > 80 or ident in seen:
            raise PolicyError(f"evidence[{index}].id must be unique and 1-80 characters")
        seen.add(ident)
        _enum(row["provenance"], PROVENANCE, f"evidence[{index}].provenance")
        for field, limit in (("observed_at", 100), ("scope", 200), ("claim", 600)):
            if not isinstance(row[field], str) or not row[field].strip() or len(row[field]) > limit:
                raise PolicyError(f"evidence[{index}].{field} is invalid")
        if not isinstance(row["material"], bool):
            raise PolicyError(f"evidence[{index}].material must be boolean")
    if value["evidence_availability"] == "unavailable" and evidence:
        raise PolicyError("unavailable evidence cannot include evidence records")
    return value


def _cost_range(path: Path | None = None) -> dict:
    table_path = path or (Path(__file__).resolve().parent.parent / "src" / "cost_table.json")
    try:
        row = json.loads(table_path.read_text(encoding="utf-8"))["controller"]
        minimum, expected, maximum = row.get("cost_min_usd"), row.get("quick_mode_run_usd"), row.get("cost_max_usd")
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        minimum = expected = maximum = None
    return {"currency": "USD", "minimum": minimum, "expected": expected, "maximum": maximum,
            "allowance_cap": DEFAULT_CONTROLLER_ALLOWANCE_USD}


def _recommendation(assessment: dict) -> tuple[str, list[str]]:
    consequence = assessment["consequence"]
    uncertainty = assessment["premise_uncertainty"]
    alternatives = assessment["alternatives"]
    coupling = assessment["constraint_coupling"]
    failure = assessment["observed_failure_cause"]
    evidence = assessment["evidence"]
    material_evidence = any(row["material"] for row in evidence)

    if assessment["required_output"] == "clarification":
        return "clarify", ["operator_decision_required"]
    if uncertainty == "unavailable" and assessment["evidence_availability"] == "unavailable":
        return "clarify", ["material_evidence_unavailable"]
    if failure == "premise-conflict":
        return "controller", ["new_material_premise_conflict"]
    contradiction_material = (
        uncertainty == "contradictory" and material_evidence
        and (consequence in ("consequential", "irreversible")
             or alternatives != "one-established" or coupling != "local")
    )
    if contradiction_material:
        return "controller", ["material_checkable_contradiction"]
    high_consequence = consequence in ("consequential", "irreversible")
    unresolved = uncertainty in ("specific-checkable", "contradictory")
    material_choice = alternatives in ("several-material", "unknown") or coupling in ("cross-module", "cross-system")
    if high_consequence and unresolved and material_choice:
        return "controller", ["consequential_unresolved_material_alternatives"]
    reasons = ["clear_worker_frame"]
    if failure == "implementation":
        reasons.append("implementation_failure_worker_repair")
    elif failure == "infrastructure":
        reasons.append("infrastructure_failure_not_rigour_signal")
    elif failure == "context-overflow":
        reasons.append("context_overflow_requires_handoff")
    return "worker", reasons


def decide(assessment_value: object, control: controller_control.ControlDecision, *,
           selected_cell: str = "worker-sonnet-low", controller_profile: str = "standard",
           prior_controller_invocations: int = 0, public_passed: bool = False,
           cost_table_path: Path | None = None) -> dict:
    """Return a complete immutable RoutingDecision without dispatching work."""
    assessment = validate_assessment(assessment_value)
    model_registry.resolve_cell(selected_cell)
    model_registry.resolve_role_profile(controller_profile)
    if type(prior_controller_invocations) is not int or prior_controller_invocations < 0:
        raise PolicyError("prior_controller_invocations must be a non-negative integer")
    if control.task_revision is not None and control.task_revision != assessment["task_revision"]:
        raise PolicyError("control snapshot belongs to a different task revision")
    recommendation, reasons = _recommendation(assessment)
    effective = recommendation
    if recommendation != "clarify":
        if control.mode == "on":
            effective = "controller"
            reasons.append("operator_forced_controller")
        elif control.mode == "off":
            effective = "worker"
            reasons.append("operator_excluded_controller")

    costs = _cost_range(cost_table_path)
    remaining = assessment["authorised_task_budget_usd"]
    qualification = "provisional"
    if effective == "controller" and prior_controller_invocations >= CONTROLLER_INVOCATION_LIMIT:
        effective = "blocked"
        qualification = "unavailable"
        reasons.append("controller_invocation_limit")
    elif effective == "controller" and (remaining is None or remaining < DEFAULT_CONTROLLER_ALLOWANCE_USD):
        effective = "blocked"
        qualification = "budget-blocked"
        reasons.append("controller_budget_unknown" if remaining is None else "controller_budget_insufficient")
    elif effective == "clarify":
        qualification = "unavailable"

    high_risk_unresolved = (
        assessment["consequence"] in ("consequential", "irreversible")
        and assessment["premise_uncertainty"] != "none"
        and assessment["verification_gap"] != "strong-existing-checks"
    )
    if public_passed and high_risk_unresolved:
        reasons.append("visible_pass_does_not_close_rigour_gap")

    evidence_ids = [row["id"] for row in assessment["evidence"]]
    body = {
        "decision_version": DECISION_VERSION,
        "task_revision": assessment["task_revision"], "policy_id": POLICY_ID,
        "assessment_digest": digest(assessment), "recommended_action": recommendation,
        "effective_action": effective, "selected_cell": selected_cell,
        "controller_profile": controller_profile, "override_mode": control.mode,
        "override_scope": control.source, "override_revision": control.state_revision,
        "reason_codes": reasons, "evidence_ids": evidence_ids,
        "qualification_status": qualification, "cost_range": costs,
        "remaining_budget": remaining,
        "next_checkpoint": (
            "operator-clarification" if effective == "clarify" else
            "budget-or-policy-resolution" if effective == "blocked" else
            "controller-evidence-validation" if effective == "controller" else
            "worker-visible-acceptance"
        ),
        "public_pass_observed": public_passed,
        "required_rigour_check_complete": not high_risk_unresolved,
    }
    body["decision_id"] = "rtd-" + digest(body)[:24]
    return body
