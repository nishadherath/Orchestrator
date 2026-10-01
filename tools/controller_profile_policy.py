"""Versioned, evidence-conservative Controller role-profile selection.

There is no qualified task-family evidence for the frontier profile yet. The
automatic rule therefore retains the standard profile. A frontier trial needs
an explicit experimental root and request, and its budget check establishes
only admission capacity, not that every role call will finish under the cap.
"""
from __future__ import annotations

import math

import controller_policy
import model_registry


POLICY_ID = "controller-profile-v1"
CONTROLLER_ALLOWANCE_V1_USD = 4.0


class ProfilePolicyError(ValueError):
    """A role profile cannot be selected under the supplied authority."""


def choose(*, remaining_usd: float, experimental_admission: bool,
           requested_profile: str | None = None,
           explicit_experimental: bool = False,
           follow_on_floor_usd: float) -> dict:
    """Select one role profile before a Controller routing decision is frozen."""
    if (type(remaining_usd) not in (int, float) or not math.isfinite(remaining_usd)
            or remaining_usd < 0 or type(follow_on_floor_usd) not in (int, float)
            or not math.isfinite(follow_on_floor_usd)
            or follow_on_floor_usd <= 0 or type(experimental_admission) is not bool
            or type(explicit_experimental) is not bool):
        raise ProfilePolicyError("profile budget or admission input is invalid")
    if requested_profile is not None and (
            not isinstance(requested_profile, str) or not requested_profile):
        raise ProfilePolicyError("requested profile must be a non-empty name")
    if controller_policy.DEFAULT_CONTROLLER_ALLOWANCE_USD != CONTROLLER_ALLOWANCE_V1_USD:
        raise ProfilePolicyError("Controller cap changed; a new profile policy is required")
    name = requested_profile or "standard"
    try:
        profile = model_registry.resolve_role_profile(name)
    except model_registry.RegistryError as exc:
        raise ProfilePolicyError(str(exc)) from exc
    status = profile["status"]
    if requested_profile is None:
        if status != "retained-prior":
            raise ProfilePolicyError("automatic profile lacks retained baseline evidence")
        source = "automatic-retained"
    elif status == "unqualified-experimental":
        if not (experimental_admission and explicit_experimental):
            raise ProfilePolicyError(
                "unqualified profile needs an explicit experimental admission")
        required = CONTROLLER_ALLOWANCE_V1_USD + follow_on_floor_usd
        if remaining_usd < required:
            raise ProfilePolicyError(
                "experimental profile cannot reserve Controller and worker allowances")
        source = "explicit-experimental"
    elif status == "retained-prior":
        source = "explicit-retained"
    else:
        raise ProfilePolicyError("profile status has no qualified selection rule")
    return {
        "schema_version": 1, "policy_id": POLICY_ID, "profile": name,
        "registry_status": status, "source": source,
        "remaining_usd_at_selection": remaining_usd,
        "controller_allowance_usd": CONTROLLER_ALLOWANCE_V1_USD,
        "follow_on_floor_usd": follow_on_floor_usd,
        "experimental_admission": experimental_admission,
        "qualification_claim": "none" if status == "unqualified-experimental"
        else "retained-prior-only",
    }


def validate(value: object) -> dict:
    """Validate a frozen v1 selection without reopening current registry state.

    Admission separately compares against `choose` on the current registry.
    A later registry update must not make an already admitted root unreadable.
    """
    if not isinstance(value, dict) or set(value) != {
            "schema_version", "policy_id", "profile", "registry_status", "source",
            "remaining_usd_at_selection", "controller_allowance_usd",
            "follow_on_floor_usd", "experimental_admission", "qualification_claim"}:
        raise ProfilePolicyError("role-profile selection fields are invalid")
    if value["schema_version"] != 1 or value["policy_id"] != POLICY_ID:
        raise ProfilePolicyError("unsupported role-profile selection policy")
    if (type(value["remaining_usd_at_selection"]) not in (int, float)
            or not math.isfinite(value["remaining_usd_at_selection"])
            or value["remaining_usd_at_selection"] < 0
            or type(value["follow_on_floor_usd"]) not in (int, float)
            or not math.isfinite(value["follow_on_floor_usd"])
            or value["follow_on_floor_usd"] <= 0
            or value["controller_allowance_usd"] != CONTROLLER_ALLOWANCE_V1_USD
            or type(value["experimental_admission"]) is not bool):
        raise ProfilePolicyError("frozen profile budget or admission is invalid")
    ordinary = (value["profile"] == "standard"
                and value["registry_status"] == "retained-prior"
                and value["source"] in {"automatic-retained", "explicit-retained"}
                and value["qualification_claim"] == "retained-prior-only")
    frontier = (value["profile"] == "frontier-candidate"
                and value["registry_status"] == "unqualified-experimental"
                and value["source"] == "explicit-experimental"
                and value["experimental_admission"] is True
                and value["qualification_claim"] == "none"
                and value["remaining_usd_at_selection"] >=
                value["controller_allowance_usd"] + value["follow_on_floor_usd"])
    if not (ordinary or frontier):
        raise ProfilePolicyError("frozen role-profile selection is inconsistent")
    return value
