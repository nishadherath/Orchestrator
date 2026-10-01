#!/usr/bin/env python3
"""Prospective Q4U dispatch wrapper for a dedicated one-episode process.

The earlier Q4 campaign seals ``task_executor.py`` byte-for-byte. Q4U's
candidate therefore lives here and is installed only in this wrapper's
single-process admission window. Production B0 and historical snapshots are
unchanged. No Q4U runner may share this Python process with another admission.
"""
from __future__ import annotations

import hashlib
import threading
from pathlib import Path

import task_executor as base
from worker_adapter import digest
from worker_q4u_coverage import CoverageError, decision


POLICY = "Q4U-verification-v3"
ARMS = {"b0", "cross_component_medium", "coverage_repair"}
SUPPORTED = {"worker-sonnet-low", "worker-sonnet-medium", "worker-opus-high"}
_ADMISSION_LOCK = threading.Lock()


def resolve(spec: dict, capability: dict, budget_usd: float, adapter) -> dict:
    """Bind a public-only Q4U assessment to a bounded three-call ladder."""
    if (not isinstance(spec, dict)
            or set(spec) != {"schema_version", "arm", "manifest_sha256",
                             "public_assessment", "cost_ceiling_usd"}
            or spec["schema_version"] != 3 or spec["arm"] not in ARMS
            or not isinstance(spec["manifest_sha256"], str)
            or not base.SHA256.fullmatch(spec["manifest_sha256"])
            or type(budget_usd) not in (int, float) or budget_usd <= 0
            or spec["cost_ceiling_usd"] != budget_usd):
        raise base.ExecutorError("invalid Q4U experimental dispatch contract")
    if (capability.get("enforcement_proven") is not True
            and getattr(adapter, "offline_fake", False) is not True):
        raise base.ExecutorError("Q4U dispatch needs an enforced host or fake")
    supported = capability.get("supported_cells")
    if (not isinstance(supported, list) or len(supported) != len(set(supported))
            or any(not isinstance(cell, str) for cell in supported)
            or capability.get("budget_enforced") is not True):
        raise base.ExecutorError("Q4U host cells or budget enforcement are invalid")
    public = spec["public_assessment"]
    if (not isinstance(public, dict)
            or set(public) != {"schema_version", "task_id", "task_sha256", "assessment"}
            or public["schema_version"] != 1
            or not isinstance(public["task_sha256"], str)
            or not base.SHA256.fullmatch(public["task_sha256"])):
        raise base.ExecutorError("Q4U public assessment envelope is invalid")
    assessment = public["assessment"]
    files = assessment.get("public_file_sha256") if isinstance(assessment, dict) else None
    actor_root = capability.get("actor_root")
    if not isinstance(actor_root, str) or not actor_root:
        raise base.ExecutorError("Q4U actor root is unavailable")
    root = Path(actor_root)
    if (not isinstance(files, dict) or set(files) != {"ISSUE.md", "public_check.py"}
            or any(not isinstance(expected, str)
                   or not base.SHA256.fullmatch(expected)
                   or not (root / name).is_file()
                   or hashlib.sha256((root / name).read_bytes()).hexdigest() != expected
                   for name, expected in files.items())):
        raise base.ExecutorError("Q4U cited public bytes differ from actor")
    try:
        initial = decision(assessment, policy=spec["arm"], phase="initial",
                           low_outcome=None, supported_cells=set(supported),
                           remaining_usd=budget_usd, call_ceiling_usd=budget_usd,
                           budget_enforced=True)
        second = (decision(assessment, policy=spec["arm"], phase="after_low",
                           low_outcome="verification_failed",
                           supported_cells=set(supported),
                           remaining_usd=budget_usd, call_ceiling_usd=budget_usd,
                           budget_enforced=True) if initial["action"] == "worker-sonnet-low"
                  else {"action": "worker-sonnet-low", "reason": "repair_after_medium"})
    except (CoverageError, KeyError, TypeError, ValueError) as exc:
        raise base.ExecutorError(f"invalid Q4U public assessment: {exc}") from exc
    ladder = [initial["action"], second["action"], "worker-opus-high"]
    if (set(ladder) - set(supported) or "stop" in ladder
            or not set(ladder) <= SUPPORTED):
        raise base.ExecutorError("Q4U host cannot fund or serve the frozen ladder")
    return {"schema_version": 3, "policy": POLICY, "arm": spec["arm"],
            "manifest_sha256": spec["manifest_sha256"],
            "assessment_digest": assessment["assessment_sha256"],
            "evidence_cohort": "Q4U-public-only",
            "selection_digest": digest({"initial": initial,
                                        "after_first_failure": second}),
            "selected_cell": ladder[0], "eligible_cells": sorted(supported),
            "cost_ceiling_usd": budget_usd, "ladder": ladder,
            "after_first_failure": ladder[1],
            "public_task_sha256": public["task_sha256"]}


class Q4UTaskExecutor(base.TaskExecutor):
    """Run Q4U's v3 ladder without changing the shared executor source."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base.EXPERIMENTAL_POLICIES.add(POLICY)

    def admit(self, *, experimental_dispatch: dict, **kwargs) -> str:
        if not isinstance(experimental_dispatch, dict):
            raise base.ExecutorError("Q4U admission requires a frozen v3 dispatch")
        with _ADMISSION_LOCK:
            original = base._experimental_policy
            base._experimental_policy = resolve
            try:
                return super().admit(experimental_dispatch=experimental_dispatch,
                                     **kwargs)
            finally:
                base._experimental_policy = original
