#!/usr/bin/env python3
"""N3 worker-only assessor and shadow selector.

Inputs are structured, public task facts supplied by the existing assessment
turn. This module never reads task prose, hidden grades, or Controller state and
never launches a provider. Its labelled priors are candidates for N5, not a
claim of measured superiority over the qualified B0 executor.
"""
from __future__ import annotations

import math
from typing import Any

import model_registry
from worker_adapter import digest


POLICY = "worker-shadow-v1"
FIELDS = {"task_kind", "complexity", "verification", "context_tokens",
          "deadline_seconds", "failure_cause", "prior_local_repairs",
          "frame_confidence", "required_artefacts", "evidence"}
EVIDENCE_FIELDS = {"source", "reference", "claim"}
OVERRIDE_FIELDS = {"cell", "actor", "authority_id", "reason", "max_cost_usd"}
FAILURES = {"none", "local_failure", "context_overflow", "missing_facts",
            "infrastructure", "permission", "identity", "accounting"}
PRIORS = {"routine": "worker-sonnet-low", "moderate": "worker-sonnet-high",
          "complex": "worker-opus-high"}
ALTERNATIVES = {
    "routine": ("worker-sonnet-medium", "worker-opus-low"),
    "moderate": ("worker-sonnet-medium", "worker-opus-medium", "worker-fable-medium"),
    "complex": ("worker-sonnet-xhigh", "worker-opus-medium", "worker-fable-high"),
}


class AssessmentError(ValueError):
    """The public assessment is incomplete, ambiguous or contaminated."""


def _exact_keys(value: Any, keys: set[str], name: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise AssessmentError(f"{name} must have exactly {sorted(keys)}")


def assess(facts: dict) -> dict:
    """Validate a structured public assessment without interpreting wording."""
    _exact_keys(facts, FIELDS, "assessment")
    for field, choices in (("task_kind", {"implementation", "investigation"}),
                           ("complexity", set(PRIORS)),
                           ("verification", {"executable", "manual", "none"}),
                           ("failure_cause", FAILURES),
                           ("frame_confidence", {"clear", "uncertain"})):
        if facts[field] not in choices:
            raise AssessmentError(f"invalid {field}")
    tokens = facts["context_tokens"]
    if type(tokens) is not int or tokens < 0:
        raise AssessmentError("context_tokens must be a non-negative integer")
    deadline = facts["deadline_seconds"]
    if deadline is not None and (type(deadline) not in (int, float)
                                 or not math.isfinite(deadline) or deadline <= 0):
        raise AssessmentError("deadline_seconds must be positive or null")
    repairs = facts["prior_local_repairs"]
    if type(repairs) is not int or repairs < 0:
        raise AssessmentError("prior_local_repairs must be a non-negative integer")
    artefacts = facts["required_artefacts"]
    if not isinstance(artefacts, list) or not artefacts or any(
            not isinstance(item, str) or not item.strip() for item in artefacts):
        raise AssessmentError("required_artefacts need public non-empty names")
    evidence = facts["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise AssessmentError("at least one public evidence item is required")
    for item in evidence:
        _exact_keys(item, EVIDENCE_FIELDS, "evidence item")
        if item["source"] not in {"operator", "repository", "public_test", "public_tool"}:
            raise AssessmentError("evidence source must be public")
        if any(not isinstance(item[key], str) or not item[key].strip()
               for key in ("reference", "claim")):
            raise AssessmentError("evidence reference and claim are required")
    # Only the discriminating public facts enter the cohort. References and
    # prose are retained for audit, but cannot encode benchmark IDs or labels.
    cohort = digest({key: facts[key] for key in FIELDS - {"evidence"}})
    return {"schema_version": 1, "policy": POLICY, "facts": facts,
            "evidence_cohort": cohort, "assessment_digest": digest(facts)}


def _override(value: dict | None) -> dict | None:
    if value is None:
        return None
    _exact_keys(value, OVERRIDE_FIELDS, "override")
    for key in ("cell", "actor", "authority_id", "reason"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise AssessmentError(f"override {key} is required")
    maximum = value["max_cost_usd"]
    if maximum is not None and (type(maximum) not in (int, float)
                                or not math.isfinite(maximum) or maximum <= 0):
        raise AssessmentError("override max_cost_usd must be positive or null")
    try:
        model_registry.resolve_cell(value["cell"])
    except model_registry.RegistryError as exc:
        raise AssessmentError(str(exc)) from exc
    return value


def select(assessment: dict, *, supported_cells: set[str],
           remaining_usd: float, budget_enforced: bool,
           override: dict | None = None) -> dict:
    """Resolve every cell and choose a shadow candidate or an explicit stop.

    `supported_cells` is a host assertion for this session, not a registry
    inference. Unknown projected costs require an operator ceiling and a host
    that enforces it. No cache savings are presumed. Selection has no dispatch
    side effect; N5 must qualify it before B0 can be changed.
    """
    if assessment != assess(assessment.get("facts")):
        raise AssessmentError("assessment digest, schema or policy mismatch")
    requested = _override(override)
    if type(remaining_usd) not in (int, float) or not math.isfinite(remaining_usd) or remaining_usd < 0:
        raise AssessmentError("remaining_usd must be finite and non-negative")
    if type(budget_enforced) is not bool or not isinstance(supported_cells, set):
        raise AssessmentError("explicit host support and budget enforcement are required")
    registry = model_registry.load()
    all_cells = set(registry["cells"])
    if not supported_cells <= all_cells:
        raise AssessmentError("host listed an unsupported cell")
    facts = assessment["facts"]
    cause = facts["failure_cause"]
    stop = ("unresolved_frame" if facts["frame_confidence"] == "uncertain" else
            "clarification" if cause == "missing_facts" else
            "decompose" if cause == "context_overflow" else
            "blocked_host" if cause in {"infrastructure", "permission", "identity", "accounting"} else
            "repair_exhausted" if cause == "local_failure" and facts["prior_local_repairs"] >= 1 else
            "verification_missing" if facts["verification"] == "none" else None)
    prior = PRIORS[facts["complexity"]]
    if facts["context_tokens"] > model_registry.resolve_cell(prior, registry)["context_limit_tokens"]:
        stop = "decompose"
    rows = []
    for model in registry["model_order"]:
        for effort in registry["effort_order"]:
            name = f"worker-{model}-{effort}"
            cell = model_registry.resolve_cell(name, registry)
            projection = model_registry.projected_cost(name, registry=registry)
            reasons = []
            if not cell["direct_worker"]:
                reasons.append("not_direct_worker")
            if name not in supported_cells:
                reasons.append("host_unsupported")
            if not budget_enforced:
                reasons.append("budget_not_enforced")
            if facts["context_tokens"] > cell["context_limit_tokens"]:
                reasons.append("context_limit")
            if projection["known"]:
                if projection["cost_per_run_usd"] > remaining_usd:
                    reasons.append("projected_cost_exceeds_remaining")
                if (facts["deadline_seconds"] is not None
                        and projection["wall_clock_s"] > facts["deadline_seconds"]):
                    reasons.append("projected_wall_exceeds_deadline")
            else:
                reasons.append("cost_or_wall_unknown")
                if facts["deadline_seconds"] is not None:
                    reasons.append("wall_unknown_with_deadline")
            if cell["availability"]["status"] != "observed":
                reasons.append("availability_unverified")
            operational_reasons = list(reasons)
            if name != prior and requested is None:
                reasons.append("not_prior_choice")
            if requested is not None and name != requested["cell"]:
                reasons.append("not_override_choice")
            if requested is not None and name == requested["cell"]:
                ceiling = requested["max_cost_usd"]
                if ceiling is None and not projection["known"]:
                    reasons.append("unknown_cost_requires_ceiling")
                if ceiling is not None and ceiling > remaining_usd:
                    reasons.append("override_ceiling_exceeds_remaining")
                if (projection["known"] and ceiling is not None
                        and projection["cost_per_run_usd"] > ceiling):
                    reasons.append("projection_exceeds_override_ceiling")
                # An explicit experimental request may inspect a configured
                # but unverified model; it never asserts live availability.
                if "availability_unverified" in reasons:
                    reasons.remove("availability_unverified")
                if "cost_or_wall_unknown" in reasons and ceiling is not None:
                    reasons.remove("cost_or_wall_unknown")
            rows.append({"cell": name, "model": model, "effort": effort,
                         "eligible": not reasons and stop is None,
                         "operationally_eligible": not operational_reasons and stop is None,
                         "reasons": reasons + ([stop] if stop else []),
                         "projection": projection,
                         "cost_uncertainty": ("historical_task_mean_not_current_quote"
                                              if projection["known"] else "unknown"),
                         "qualification": cell["qualification"],
                         "availability": cell["availability"]})
    chosen = next((row["cell"] for row in rows if row["eligible"]), None)
    if requested is not None and chosen is None and stop is None:
        stop = "override_rejected"
    if chosen is None and stop is None:
        stop = "no_qualified_candidate"
    return {"schema_version": 1, "policy": POLICY, "mode": "shadow",
            "selected_cell": chosen, "stop": stop,
            "evidence_cohort": assessment["evidence_cohort"],
            "assessment_digest": assessment["assessment_digest"],
            "override": requested, "override_applies_to": "future_shadow_decisions_only",
            "cache_reuse": "unknown_not_discounted",
            "prior": prior, "alternatives": list(ALTERNATIVES[facts["complexity"]]),
            "eligible_alternatives": [row["cell"] for row in rows
                                      if row["cell"] != chosen and row["operationally_eligible"]],
            "quality_basis": "unqualified_labelled_prior",
            "cells": rows}
