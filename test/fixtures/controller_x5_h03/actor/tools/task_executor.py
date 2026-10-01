#!/usr/bin/env python3
"""Durable worker executor for one root task (execution contract v2).

All changes to a root record are atomic under an OS lock. The journal inside
that record is authoritative; the current-state fields are its checked
projection. Budget operations use stable invocation ids so cross-file crashes
    can be reconciled without repeating a provider side effect. Explicit N2
    delegation remains a child of this root, never a second root scheduler.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import hashlib
import math
import sys
import threading
import re
import secrets
from pathlib import Path

import acceptance
import dispatch_budget
import model_registry
import route
import worker_selector
from worker_adapter import WorkerRequest, digest


class ExecutorError(RuntimeError):
    """A task cannot advance without new evidence or operator authority."""


EDGES = {
    "prepared": {"ready", "blocked", "cancelled"},
    "ready": {"admitted", "blocked", "cancelled"},
    "admitted": {"running", "blocked", "uncertain", "cancelled"},
    "running": {"verifying", "blocked", "uncertain", "cancelled"},
    "verifying": {"ready", "awaiting_review", "accepted", "failed", "partial", "blocked", "uncertain", "cancelled"},
    "awaiting_review": {"verifying", "blocked", "cancelled"},
    "blocked": {"ready", "verifying", "awaiting_review", "uncertain", "failed", "partial", "cancelled"},
    "uncertain": {"verifying", "blocked", "cancelled"},
    "accepted": set(), "failed": set(), "partial": set(), "cancelled": set(),
}
TERMINAL = {"accepted", "failed", "partial", "cancelled"}
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPERIMENTAL_POLICY = "N5-experimental-v1"
EXPERIMENTAL_POLICY_V2 = "Q4-first-cell-v2"
PENDING_N3_POLICY = "X4-pending-n3-v1"
EXPERIMENTAL_N3_POLICY = "X4-experimental-n3-v1"
EXPERIMENTAL_POLICIES = {EXPERIMENTAL_POLICY, EXPERIMENTAL_POLICY_V2,
                         PENDING_N3_POLICY, EXPERIMENTAL_N3_POLICY}


def _experimental_policy(spec: dict, capability: dict, budget_usd: float,
                         adapter, baseline_ladder: list[str] | None = None) -> dict:
    """Resolve a campaign-only arm at admission, before any paid side effect.

    The caller must validate the frozen campaign manifest and operator approval.
    This boundary additionally requires a proved host (or an explicit fake),
    public assessment, supported cells and a task-level cost ceiling. A digest
    of the resolved choice is frozen into the root and every attempt decision.
    """
    if not isinstance(spec, dict) or spec.get("schema_version") not in {1, 2, 3}:
        raise ExecutorError("invalid experimental dispatch contract")
    version = spec["schema_version"]
    common = {"schema_version", "arm", "manifest_sha256", "assessment",
              "alternative_cell", "cost_ceiling_usd"}
    keys = ({"schema_version", "arm", "manifest_sha256", "cost_ceiling_usd",
             "repair_cells"} if version == 3 else
            (common | {"fallback_cell"}) if version == 1 else
            (common | {"repair_cells"}))
    if set(spec) != keys:
        raise ExecutorError("invalid experimental dispatch contract")
    if (spec["arm"] not in {"candidate", "alternative"}
            or not isinstance(spec["manifest_sha256"], str)
            or not SHA256.fullmatch(spec["manifest_sha256"])):
        raise ExecutorError("experimental arm needs a frozen campaign manifest")
    if (type(budget_usd) not in (int, float)
            or type(spec["cost_ceiling_usd"]) not in (int, float)
            or spec["cost_ceiling_usd"] != budget_usd
            or budget_usd <= 0):
        raise ExecutorError("experimental cost ceiling must equal the root budget")
    if (capability.get("enforcement_proven") is not True
            and getattr(adapter, "offline_fake", False) is not True):
        raise ExecutorError("experimental dispatch needs an enforced host or fake")
    supported = capability.get("supported_cells")
    if (not isinstance(supported, list)
            or any(not isinstance(cell, str) for cell in supported)
            or len(supported) != len(set(supported))
            or capability.get("budget_enforced") is not True):
        raise ExecutorError("experimental host must declare cells and budget enforcement")
    if version == 3:
        repairs = spec["repair_cells"]
        if (spec["arm"] != "candidate"
                or repairs != ["worker-sonnet-low", "worker-opus-high"]
                or not isinstance(baseline_ladder, list)
                or len(baseline_ladder) != 3
                or any(cell not in supported for cell in baseline_ladder + repairs)):
            raise ExecutorError("deferred N3 selection needs a supported B0 and repair ladder")
        return {"schema_version": 3, "policy": PENDING_N3_POLICY,
                "arm": "candidate", "manifest_sha256": spec["manifest_sha256"],
                "assessment_digest": None, "selection_digest": None,
                "selected_cell": None, "eligible_cells": sorted(supported),
                "cost_ceiling_usd": budget_usd, "ladder": baseline_ladder,
                "common_repair_tail": repairs}
    try:
        assessment = worker_selector.assess(spec["assessment"]["facts"])
        if assessment != spec["assessment"]:
            raise ExecutorError("experimental assessment changed")
        override = None
        if spec["arm"] == "alternative":
            override = {"cell": spec["alternative_cell"], "actor": "n5-development",
                        "authority_id": spec["manifest_sha256"],
                        "reason": "predeclared bounded comparison arm",
                        "max_cost_usd": budget_usd}
        selection = worker_selector.select(
            assessment, supported_cells=set(supported), remaining_usd=budget_usd,
            budget_enforced=True, override=override)
    except (KeyError, TypeError, worker_selector.AssessmentError) as exc:
        raise ExecutorError(f"invalid experimental assessment: {exc}") from exc
    if selection["stop"] is not None:
        raise ExecutorError(f"experimental selector stopped: {selection['stop']}")
    if spec["arm"] == "candidate":
        if spec["alternative_cell"] is not None:
            raise ExecutorError("candidate arm cannot supply an alternative cell")
        selected = selection["selected_cell"]
    else:
        selected = spec["alternative_cell"]
        row = next((row for row in selection["cells"] if row["cell"] == selected), None)
        if row is None or not row["eligible"] or selection["selected_cell"] != selected:
            raise ExecutorError("alternative cell is not operationally eligible")
    operational = {row["cell"] for row in selection["cells"]
                   if row["operationally_eligible"]}
    if version == 1:
        fallback = spec["fallback_cell"]
        if fallback not in operational:
            raise ExecutorError("experimental fallback is unsupported")
        ladder = [selected, selected, fallback]
        policy_name = EXPERIMENTAL_POLICY
        extra = {}
    else:
        repairs = spec["repair_cells"]
        if (repairs != ["worker-sonnet-low", "worker-opus-high"]
                or any(cell not in operational for cell in repairs)):
            raise ExecutorError("Q4 common repair tail is unsupported or changed")
        ladder = [selected, *repairs]
        policy_name = EXPERIMENTAL_POLICY_V2
        extra = {"common_repair_tail": repairs}
    return {"schema_version": version, "policy": policy_name,
            "arm": spec["arm"], "manifest_sha256": spec["manifest_sha256"],
            "assessment_digest": assessment["assessment_digest"],
            "evidence_cohort": assessment["evidence_cohort"],
            "selection_digest": digest(selection), "selected_cell": selected,
            "eligible_cells": sorted(operational),
            "cost_ceiling_usd": budget_usd, "ladder": ladder, **extra}


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        checksum = value.pop("record_digest")
        if (value.get("schema_version") != 2 or value.get("record_type") != "TaskRoot"
                or checksum != digest(value)):
            raise ValueError("invalid task record digest or header")
        definition = value["definition"]
        revision = value["revision"]
        if (value["definition_digest"] != digest(definition)
                or revision["definition_digest"] != value["definition_digest"]
                or revision["revision_id"] != digest({**{k: v for k, v in revision.items()
                                                        if k != "revision_id"},
                                                     "task_id": value["task_id"]})):  # immutable identity
            raise ValueError("definition or revision digest mismatch")
        frozen = definition["acceptance_definition"]
        baseline = frozen["protected_baseline"]
        if (frozen["contract_version"] != acceptance.CONTRACT_VERSION
                or frozen["contract_digest"] != acceptance.digest(frozen["contract"])
                or baseline["digest"] != acceptance.digest(
                    {"files": baseline["files"], "missing": baseline["missing"]})):
            raise ValueError("frozen acceptance digest mismatch")
        previous = None
        for n, event in enumerate(value["journal"], 1):
            if (event["sequence"] != n or event["previous_digest"] != previous
                    or event["digest"] != digest({k: v for k, v in event.items() if k != "digest"})):
                raise ValueError(f"invalid journal event {n}")
            previous = event["digest"]
        delegation = value.get("delegation")
        if delegation is not None and (delegation.get("version") != 1
                or delegation.get("plan_digest") != digest(delegation.get("plan"))
                or delegation["plan"].get("root_revision_id") != revision["revision_id"]):
            raise ValueError("delegation plan digest or revision mismatch")
        public_assessment = value.get("public_assessment")
        if public_assessment is not None:
            fields = {"version", "revision_id", "invocation_id", "packet_sha256",
                      "status", "result", "result_digest"}
            if (not isinstance(public_assessment, dict)
                    or set(public_assessment) not in (fields, fields | {"reconciliation"})
                    or public_assessment["version"] != 1
                    or public_assessment["revision_id"] != revision["revision_id"]
                    or not isinstance(public_assessment["packet_sha256"], str)
                    or not SHA256.fullmatch(public_assessment["packet_sha256"])
                    or public_assessment["status"] not in {
                        "intent", "started", "uncertain", "invalid", "settled"}
                    or (public_assessment["status"] == "settled" and (
                        not isinstance(public_assessment["result"], dict)
                        or public_assessment["result_digest"] !=
                        digest(public_assessment["result"])))
                    or (public_assessment["status"] != "settled" and (
                        public_assessment["result"] is not None
                        or public_assessment["result_digest"] is not None))
                    or not any(event["kind"] == "public_assessment_admitted"
                               and event["data"].get("invocation_id") ==
                               public_assessment["invocation_id"]
                               for event in value["journal"])):
                raise ValueError("public assessment admission or result is malformed")
            reconciliation = public_assessment.get("reconciliation")
            if reconciliation is not None and (
                    public_assessment["status"] != "invalid"
                    or not isinstance(reconciliation, dict)
                    or set(reconciliation) != {"actor", "reason", "cost_usd",
                                              "evidence", "writers_stopped"}
                    or any(not isinstance(reconciliation[key], str)
                           or not reconciliation[key].strip()
                           for key in ("actor", "reason", "evidence"))
                    or reconciliation["writers_stopped"] is not True
                    or type(reconciliation["cost_usd"]) not in (int, float)
                    or not math.isfinite(reconciliation["cost_usd"])
                    or reconciliation["cost_usd"] < 0
                    or not any(event["kind"] == "public_assessment_reconciled"
                               and event["data"].get("invocation_id") ==
                               public_assessment["invocation_id"]
                               and event["data"].get("reconciliation_digest") ==
                               digest(reconciliation)
                               for event in value["journal"])):
                raise ValueError("public assessment reconciliation is malformed")
        routing = value.get("routing_decision")
        if routing is not None:
            import controller_profile_policy

            decision = routing.get("decision") if isinstance(routing, dict) else None
            control = routing.get("control") if isinstance(routing, dict) else None
            version = routing.get("version") if isinstance(routing, dict) else None
            required = ({"version", "decision", "decision_digest", "control"}
                        if version == 1 else
                        {"version", "decision", "decision_digest", "control",
                         "profile_selection"} if version == 2 else set())
            selection = routing.get("profile_selection") if isinstance(routing, dict) else None
            if (not isinstance(routing, dict)
                    or set(routing) != required
                    or not isinstance(decision, dict)
                    or routing["decision_digest"] != digest(decision)
                    or decision.get("decision_id") != "rtd-" + digest({
                        key: item for key, item in decision.items()
                        if key != "decision_id"})[:24]
                    or not isinstance(control, dict)
                    or set(control) != {"mode", "source", "state_revision",
                                        "task_revision", "session_id"}
                    or decision.get("override_mode") != control["mode"]
                    or decision.get("override_scope") != control["source"]
                    or decision.get("override_revision") != control["state_revision"]
                    or decision.get("task_revision") != control["task_revision"]
                    or not isinstance(public_assessment, dict)
                    or public_assessment["status"] != "settled"
                    or decision.get("assessment_digest") != digest(
                        public_assessment["result"]["rigour"])
                    or decision.get("selected_cell") != value["ladder"][0]
                    or (version == 2 and (
                        controller_profile_policy.validate(selection)["profile"] !=
                        decision.get("controller_profile")
                        or selection["remaining_usd_at_selection"] !=
                        decision.get("remaining_budget")
                        or selection["experimental_admission"] !=
                        (value["admission"]["policy"] == EXPERIMENTAL_N3_POLICY)))
                    or decision.get("effective_action") not in {
                        "worker", "controller", "blocked", "clarify"}
                    or not any(event["kind"] == "routing_decision_frozen"
                               and event["data"].get("decision_id") ==
                               decision.get("decision_id")
                               and (version == 1 or (
                                   event["data"].get("profile_policy") ==
                                   selection["policy_id"]
                                   and event["data"].get("profile_source") ==
                                   selection["source"]))
                               for event in value["journal"])):
                raise ValueError("routing decision differs from frozen assessment or control")
        controller = value.get("controller_admission")
        if controller is not None:
            base = {"revision_id", "decision_id", "invocation_id",
                        "follow_on_invocation_id",
                        "controller_task_revision", "allowance_usd",
                        "follow_on_floor_usd", "status"}
            version = controller.get("version", 1) if isinstance(controller, dict) else None
            required = base if version == 1 else base | {"version"} if version == 2 else set()
            if version == 2 and controller.get("status") == "worker-ready":
                required |= {"handoff", "handoff_digest"}
            if (not isinstance(controller, dict) or set(controller) != required
                    or controller["revision_id"] != revision["revision_id"]
                    or not isinstance(controller["controller_task_revision"], str)
                    or not SHA256.fullmatch(controller["controller_task_revision"])
                    or controller["status"] not in ({"intent", "started"}
                                                    if version == 1 else
                                                    {"intent", "started", "worker-ready"})
                    or (controller["status"] == "worker-ready" and
                        (not isinstance(controller["handoff"], dict)
                         or controller["handoff_digest"] != digest(controller["handoff"])
                         or controller["handoff"].get("handoff_digest") !=
                         digest({key: item for key, item in controller["handoff"].items()
                                 if key != "handoff_digest"})
                         or controller["handoff"].get("task_revision") !=
                         controller["controller_task_revision"]
                         or controller["handoff"].get("selected_cell") != value["ladder"][0]))
                    or not any(event["kind"] == "controller_admitted"
                               and event["data"].get("decision_id") == controller["decision_id"]
                               for event in value["journal"])):
                raise ValueError("Controller admission is malformed or not journalled")
        if value["admission"]["policy"] in EXPERIMENTAL_POLICIES:
            policy = value.get("experimental_policy")
            if (not isinstance(policy, dict)
                    or policy.get("policy") != value["admission"]["policy"]
                    or value["admission"]["policy_digest"] != digest(policy)
                    or value["ladder"] != policy.get("ladder")):
                raise ValueError("experimental policy digest or ladder mismatch")
            if policy["policy"] == PENDING_N3_POLICY and (
                    policy.get("schema_version") != 3
                    or policy.get("selected_cell") is not None
                    or policy.get("assessment_digest") is not None):
                raise ValueError("pending N3 policy has a selected cell")
            if policy["policy"] == EXPERIMENTAL_N3_POLICY and (
                    policy.get("schema_version") != 3
                    or not isinstance(policy.get("selected_cell"), str)
                    or policy["selected_cell"] != value["ladder"][0]
                    or not isinstance(value.get("public_assessment"), dict)
                    or value["public_assessment"]["status"] != "settled"
                    or policy.get("assessment_digest") != value[
                        "public_assessment"]["result"]["worker"]["assessment_digest"]):
                raise ValueError("frozen N3 policy differs from the charged assessment")
        return value
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ExecutorError(f"Unreadable task record {path}: {exc}; preserve and reconcile") from exc


def _write(path: Path, value: dict) -> None:
    payload = {**value, "record_digest": digest(value)}
    route._atomic_write_bytes(path, (json.dumps(payload, indent=2, allow_nan=False) + "\n").encode())


def _event(value: dict, kind: str, **data: object) -> None:
    previous = value["journal"][-1]["digest"] if value["journal"] else None
    row = {"sequence": len(value["journal"]) + 1, "previous_digest": previous,
           "kind": kind, "at": acceptance.utc_now(), "data": data}
    row["digest"] = digest(row)
    value["journal"].append(row)


def transition(value: dict, destination: str, *, reason: str = "") -> None:
    current = value["state"]
    if destination not in EDGES.get(current, set()):
        raise ExecutorError(f"forbidden task transition {current} -> {destination}")
    value["state"] = destination
    _event(value, "transition", source=current, target=destination, reason=reason)


def _definition(project_id: str, root_id: str, task_id: str, goal: str,
                scope: list[str], permissions: list[str], input_revision: dict,
                frozen: dict) -> dict:
    return {"project_id": project_id, "root_task_id": root_id, "task_id": task_id,
            "parent_task_id": None, "goal": goal, "scope": scope,
            "permissions": permissions, "input_revision": input_revision,
            "acceptance_definition": {key: frozen[key] for key in
                                      ("contract_version", "contract", "contract_digest", "protected_baseline")}}


def _declared_worker_call_cap(capability: dict) -> float | None:
    """Validate a host's per-invocation ceiling before reserving task money.

    The root budget remains task-wide. A host that admits only a smaller
    single call must not receive the entire remaining task allowance as that
    call's --max-budget-usd argument.
    """
    cap = capability.get("max_single_call_usd")
    if cap is None:
        return None
    if (type(cap) not in (int, float) or not math.isfinite(cap)
            or dispatch_budget.units(cap) <= 0):
        raise ExecutorError("worker host single-call ceiling is invalid")
    return float(cap)


def legacy_attempt(sidecar: dict, sequence: int) -> dict:
    """Allowlisted compatibility projection; rich sidecar is never ledger input."""
    receipt = sidecar.get("receipt") or {}
    verification = sidecar.get("verification") or {}
    status = ("interrupted" if sidecar.get("process_state") == "uncertain" else
              "pending" if sidecar.get("process_state") == "reserved" else
              "running" if sidecar.get("process_state") == "intent_committed" else
              receipt.get("status", "interrupted"))
    if status not in {"completed", "failed", "cancelled", "interrupted", "pending", "running"}:
        status = "interrupted"
    outcome = (verification["status"] if acceptance.qualified(verification)
               and verification.get("status") in ("pass", "fail") else "unknown")
    allowed = {"invocation_id": sidecar["invocation_id"],
               "parent_invocation_id": None, "requested_cell": sidecar["requested_cell"],
               "actual_model": receipt.get("actual_model"),
               "effort_evidence": receipt.get("effort_evidence"),
               "started_at": receipt.get("started_at"), "finished_at": receipt.get("finished_at"),
               "execution_status": status, "outcome": outcome,
               "wall_clock_s": receipt.get("wall_clock_s"), "usage": receipt.get("usage")}
    return route._normalise_attempt(allowed, sequence, sidecar["requested_cell"])


def _valid_receipt(attempt: dict, receipt: dict) -> bool:
    """Do not trust a host's self-reported identity-valid boolean alone."""
    if not receipt.get("identity_valid") or receipt.get("status") != "completed":
        return False
    if not model_registry.identity_matches(attempt["requested_cell"],
                                           receipt.get("actual_model"),
                                           receipt.get("child_models")):
        return False
    effort = model_registry.resolve_cell(attempt["requested_cell"])["effort"]
    return receipt.get("effort_evidence") == f"cli-argument:{effort}"


def _settle_persisted_receipt(value: dict, budget: dispatch_budget.DispatchBudget) -> None:
    """Close the receipt-to-budget crash window before terminal cancellation."""
    if not value["attempts"]:
        return
    attempt = value["attempts"][-1]
    receipt = attempt.get("receipt") or {}
    if not (receipt.get("terminal") and receipt.get("writer_stopped")
            and receipt.get("cost_usd") is not None):
        return
    row = budget.snapshot()["invocations"].get(attempt["invocation_id"])
    if row is not None and row["state"] != "settled":
        budget.settle(attempt["invocation_id"], receipt["cost_usd"], final=True,
                      telemetry=receipt.get("usage") or {},
                      evidence=f"receipt:{attempt['receipt_digest']}")
        attempt["process_state"] = "terminal"
        _event(value, "settled_before_cancel", invocation_id=attempt["invocation_id"])


def _release_controller_hold(value: dict, budget: dispatch_budget.DispatchBudget,
                             evidence: str) -> None:
    """A Controller's downstream hold never launched a provider call."""
    controller = value.get("controller_admission")
    if controller is None:
        return
    follow_on = controller["follow_on_invocation_id"]
    row = budget.snapshot()["invocations"].get(follow_on)
    if row and row["state"] != "settled":
        budget.settle(follow_on, 0.0, final=True,
                      telemetry={"status": "not_launched"}, evidence=evidence)


def _children_intact(project: Path, delegation: dict | None) -> bool:
    """A root pass cannot silently invalidate a required accepted child."""
    if delegation is None:
        return True
    if delegation["state"] != "complete":
        return False
    for ident, child in delegation["children"].items():
        item = delegation["plan"]["items"][ident]
        result = child.get("verification")
        if child["state"] != "accepted" or not acceptance.qualified(result):
            return False
        evidence = result["evidence"]
        contract = item["acceptance_definition"]["contract"]
        if (acceptance.snapshot(project, contract["required_outputs"])["digest"]
                != evidence["artefacts"]["digest"]
                or acceptance.snapshot(project, contract["protected_paths"])["digest"]
                != item["acceptance_definition"]["protected_baseline"]["digest"]):
            return False
    return True


class TaskExecutor:
    """One-root driver with explicit recovery, no implicit provider retries."""

    def __init__(self, project: Path, adapter, *, command_runner=None,
                 campaign_prompt: str | None = None):
        self.project = project.resolve()
        self.adapter = adapter
        self.command_runner = command_runner
        if campaign_prompt is not None and (not campaign_prompt.strip()
                                            or len(campaign_prompt) > 1000):
            raise ExecutorError("campaign prompt must be bounded and non-empty")
        self.campaign_prompt = campaign_prompt
        self.base = self.project / ".claude" / "task-executor-v2"
        self.registry = self.base / "project-registry.json"

    def _path(self, root_id: str) -> Path:
        if not isinstance(root_id, str) or not ID.fullmatch(root_id):
            raise ExecutorError("root id must be an opaque safe identifier")
        return self.base / root_id / "root.json"

    def _budget(self, root_id: str, limit: float | None = None):
        return dispatch_budget.DispatchBudget(self.base / root_id / "budget.json", limit,
                                              scope="task_dispatch")

    def status(self, root_id: str) -> dict:
        value = _read(self._path(root_id))
        return {**value, "budget": self._budget(root_id).snapshot()}

    def assess_public(self, root_id: str, *, issue: str,
                      source_paths: list[str], quote_requests: list[dict],
                      interpreter, operational: dict,
                      maximum_usd: float) -> dict:
        """Charge one public interpretation to the frozen root before routing.

        The intent and budget start are durable before the interpreter runs.
        An interrupted or unaccounted call remains held and blocks the root;
        a restart never silently invokes the interpreter a second time.
        """
        import controller_public_assessment  # The assessor imports policy code.

        path = self._path(root_id)
        budget = self._budget(root_id)
        if (not callable(interpreter) or not isinstance(operational, dict)
                or type(maximum_usd) not in (int, float)
                or not 0 < maximum_usd <= budget.remaining()):
            raise ExecutorError("public assessment needs an interpreter and funded allowance")
        if (hasattr(interpreter, "allowance_usd")
                and interpreter.allowance_usd != maximum_usd):
            raise ExecutorError("interpreter cap differs from the reserved root allowance")
        preflight = getattr(interpreter, "preflight", None)
        if preflight is not None:
            if not callable(preflight):
                raise ExecutorError("public interpreter preflight is not callable")
            try:
                preflight()
            except Exception as exc:
                raise ExecutorError(f"public interpreter preflight failed: {exc}") from exc
        with route.ledger_lock(path):
            value = _read(path)
            if (value["state"] != "ready" or value.get("public_assessment") is not None
                    or value.get("controller_admission") is not None or value["attempts"]):
                raise ExecutorError("task revision is not ready for its first public assessment")
            frozen = value["definition"]
            packet = controller_public_assessment.collect(
                self.project, issue=issue, source_paths=source_paths,
                quote_requests=quote_requests,
                input_revision=frozen["input_revision"])
            issue_text = next(row["content"] for row in packet["sources"]
                              if row["path"] == packet["issue_path"])
            if issue_text != frozen["goal"]:
                raise ExecutorError("public issue differs from frozen task goal")
            revision_id = value["revision"]["revision_id"]
            invocation_id = "public-assessment-" + revision_id[:24]
            value["public_assessment"] = {
                "version": 1, "revision_id": revision_id,
                "invocation_id": invocation_id,
                "packet_sha256": packet["packet_sha256"],
                "status": "intent", "result": None, "result_digest": None}
            _event(value, "public_assessment_admitted", invocation_id=invocation_id,
                   packet_sha256=packet["packet_sha256"])
            _write(path, value)
            try:
                budget.reserve(invocation_id, maximum_usd, .000001,
                               {"revision_id": revision_id,
                                "packet_sha256": packet["packet_sha256"],
                                "allocation": "public-assessment"})
                budget.start(invocation_id)
            except dispatch_budget.BudgetError as exc:
                raise ExecutorError("public assessment claim needs reconciliation") from exc
            value["public_assessment"]["status"] = "started"
            _event(value, "public_assessment_started", invocation_id=invocation_id)
            _write(path, value)
        response = None
        charge_settled = False
        try:
            response = interpreter(packet)
            if not isinstance(response, dict) or set(response) != {
                    "interpretation", "telemetry"}:
                raise controller_public_assessment.PublicAssessmentError(
                    "interpreter response is malformed")
            # Validate telemetry and citations before trusting an assessment.
            preliminary = controller_public_assessment.assess(
                packet, response["interpretation"], operational,
                response["telemetry"])
            cost = preliminary["telemetry"]["cost_usd"]
            budget.settle(invocation_id, cost, final=True,
                          telemetry=preliminary["telemetry"],
                          evidence=f"public-assessment:{packet['packet_sha256']}")
            charge_settled = True
            after = dict(operational)
            after["authorised_task_budget_usd"] = budget.remaining()
            assessed = controller_public_assessment.assess(
                packet, response["interpretation"], after,
                response["telemetry"])
        except Exception as exc:
            terminal_charge = preliminary["telemetry"] if charge_settled else None
            observed_charge_usd = (terminal_charge["cost_usd"]
                                   if terminal_charge is not None else None)
            if not charge_settled and isinstance(response, dict):
                try:
                    terminal_charge = controller_public_assessment.validate_telemetry(
                        response.get("telemetry"))
                    budget.settle(
                        invocation_id, terminal_charge["cost_usd"], final=True,
                        telemetry={**terminal_charge, "assessment_status": "invalid"},
                        evidence=f"public-assessment-invalid:{packet['packet_sha256']}")
                    observed_charge_usd = terminal_charge["cost_usd"]
                except (controller_public_assessment.PublicAssessmentError,
                        dispatch_budget.BudgetError):
                    terminal_charge = None
            elif (not charge_settled
                  and isinstance(exc, controller_public_assessment.PublicInterpreterError)
                  and exc.cost_usd is not None):
                try:
                    budget.settle(
                        invocation_id, exc.cost_usd, final=exc.terminal,
                        telemetry={"assessment_status": "interpreter-failed",
                                   "terminal": exc.terminal},
                        evidence=f"public-interpreter-failed:{packet['packet_sha256']}")
                    observed_charge_usd = exc.cost_usd
                    terminal_charge = ({"cost_usd": exc.cost_usd}
                                       if exc.terminal else None)
                except dispatch_budget.BudgetError:
                    terminal_charge = None
            with route.ledger_lock(path):
                current = _read(path)
                if current["public_assessment"]["status"] == "started":
                    current["public_assessment"]["status"] = (
                        "invalid" if terminal_charge is not None else "uncertain")
                    _event(current, "public_assessment_invalid" if terminal_charge is not None
                           else "public_assessment_uncertain",
                           invocation_id=invocation_id, reason=str(exc)[:500],
                           cost_usd=observed_charge_usd)
                    if current["state"] == "ready":
                        current["block"] = {"reason": "public assessment evidence invalid"
                                            if terminal_charge is not None else
                                            "public assessment accounting or evidence uncertain",
                                            "resume_phase": None}
                        transition(current, "blocked", reason=current["block"]["reason"])
                    _write(path, current)
            raise ExecutorError(f"public assessment failed closed: {exc}") from exc
        with route.ledger_lock(path):
            current = _read(path)
            if current["public_assessment"]["status"] != "started":
                raise ExecutorError("public assessment was superseded during interpretation")
            current["public_assessment"].update(
                status="settled", result=assessed,
                result_digest=digest(assessed))
            _event(current, "public_assessment_settled",
                   invocation_id=invocation_id,
                   assessment_digest=current["public_assessment"]["result_digest"],
                   cost_usd=cost)
            over_allocation = (dispatch_budget.units(cost, ceiling=True) >
                               dispatch_budget.units(maximum_usd))
            if (over_allocation or budget.snapshot()["breached"]) and current["state"] == "ready":
                current["block"] = {"reason": "public assessment exceeded its allocation",
                                    "resume_phase": None}
                transition(current, "blocked", reason=current["block"]["reason"])
            _write(path, current)
        return assessed

    def reconcile_public_assessment(self, root_id: str, *, actor: str,
                                    reason: str, cost_usd: float,
                                    evidence: str, writers_stopped: bool) -> dict:
        """Finalise a blocked public call from independently retained evidence.

        This closes accounting only. The invalid assessment and task root stay
        blocked; reconciliation never authorises another call on that revision.
        """
        if (not isinstance(actor, str) or not actor.strip()
                or not isinstance(reason, str) or not reason.strip()
                or not isinstance(evidence, str) or not evidence.strip()
                or writers_stopped is not True):
            raise ExecutorError("public reconciliation needs actor, reason, evidence and stopped writers")
        try:
            dispatch_budget.units(cost_usd, ceiling=True)
        except dispatch_budget.BudgetError as exc:
            raise ExecutorError("public reconciliation cost is invalid") from exc
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            row = value.get("public_assessment") or {}
            if value["state"] != "blocked" or row.get("status") not in {"uncertain", "invalid"}:
                raise ExecutorError("public assessment is not blocked for reconciliation")
            receipt = {"actor": actor, "reason": reason, "cost_usd": cost_usd,
                       "evidence": evidence, "writers_stopped": True}
            if row.get("reconciliation") is not None:
                if row["reconciliation"] != receipt:
                    raise ExecutorError("public assessment reconciliation conflicts")
            else:
                budget = self._budget(root_id)
                budget_row = budget.snapshot()["invocations"][row["invocation_id"]]
                if budget_row["state"] == "settled":
                    if budget_row["cost_usd"] != cost_usd:
                        raise ExecutorError("public reconciliation cost conflicts with settled charge")
                else:
                    budget.settle(row["invocation_id"], cost_usd, final=True,
                                  telemetry={"assessment_status": "reconciled-invalid",
                                             "actor": actor}, evidence=evidence)
                row["status"] = "invalid"
                row["reconciliation"] = receipt
                _event(value, "public_assessment_reconciled",
                       invocation_id=row["invocation_id"], actor=actor,
                       evidence=evidence, cost_usd=cost_usd,
                       reconciliation_digest=digest(receipt))
                _write(path, value)
        return self.status(root_id)

    def freeze_public_selection(self, root_id: str) -> dict:
        """Freeze a trial N3 cell from the charged public assessment.

        This explicit experimental admission path never changes the qualified
        B0 default. The chosen cell and common repair tail become immutable
        before either Controller or worker dispatch can reserve money.
        """
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            policy = value.get("experimental_policy")
            if not isinstance(policy, dict):
                raise ExecutorError("root has no experimental N3 admission")
            if policy["policy"] == EXPERIMENTAL_N3_POLICY:
                return self.status(root_id)
            if (policy["policy"] != PENDING_N3_POLICY
                    or value["state"] != "ready" or value["attempts"]
                    or value.get("controller_admission") is not None):
                raise ExecutorError("root is not ready to freeze N3 worker selection")
            public = value.get("public_assessment")
            if public is None or public["status"] != "settled":
                raise ExecutorError("N3 selection needs a settled public assessment")
            capability = self.adapter.capability(self.project)
            if digest(capability) != value["admission"]["capability_digest"]:
                raise ExecutorError("worker host capability changed before N3 selection")
            try:
                selection = worker_selector.select(
                    public["result"]["worker"],
                    supported_cells=set(capability["supported_cells"]),
                    remaining_usd=self._budget(root_id).remaining(),
                    budget_enforced=capability["budget_enforced"] is True)
            except (KeyError, TypeError, worker_selector.AssessmentError) as exc:
                raise ExecutorError(f"N3 selection is invalid: {exc}") from exc
            if selection["stop"] is not None:
                raise ExecutorError(f"N3 selection stopped: {selection['stop']}")
            operational = {row["cell"] for row in selection["cells"]
                           if row["operationally_eligible"]}
            selected = selection["selected_cell"]
            if (selected not in operational
                    or any(cell not in operational for cell in policy["common_repair_tail"])):
                raise ExecutorError("selected or repair cell is not operationally eligible")
            ladder = [selected, *policy["common_repair_tail"]]
            frozen = {**policy, "policy": EXPERIMENTAL_N3_POLICY,
                      "assessment_digest": public["result"]["worker"]["assessment_digest"],
                      "selection_digest": digest(selection),
                      "selected_cell": selected,
                      "eligible_cells": sorted(operational),
                      "ladder": ladder}
            value["experimental_policy"] = frozen
            value["ladder"] = ladder
            value["admission"]["policy"] = EXPERIMENTAL_N3_POLICY
            value["admission"]["policy_digest"] = digest(frozen)
            _event(value, "public_worker_selection_frozen",
                   assessment_digest=frozen["assessment_digest"],
                   selection_digest=frozen["selection_digest"],
                   selected_cell=selected, policy_digest=value["admission"]["policy_digest"])
            _write(path, value)
        return self.status(root_id)

    def freeze_routing_decision(self, root_id: str, decision: dict, *,
                                session_id: str | None = None,
                                explicit_mode: str | None = None,
                                profile_selection: dict | None = None) -> dict:
        """Bind one resolved operator mode and rigour decision to the root.

        Later setting changes cannot silently turn a Controller decision into
        direct worker execution. An identical retry reads the frozen choice;
        a different choice needs a new task revision and authority.
        """
        import controller_control
        import controller_dispatch
        import controller_policy
        import controller_profile_policy

        decision = controller_dispatch._validate_decision(decision)
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            prior = value.get("routing_decision")
            if prior is not None:
                if (prior["decision"] != decision
                        or (profile_selection is not None
                            and prior.get("profile_selection") != profile_selection)):
                    raise ExecutorError("task revision already owns a different routing decision")
                return self.status(root_id)
            if (value["state"] != "ready" or value["attempts"]
                    or value.get("controller_admission") is not None
                    or value["admission"]["policy"] == PENDING_N3_POLICY):
                raise ExecutorError("task revision is not ready to freeze routing")
            public = value.get("public_assessment")
            if public is None or public["status"] != "settled":
                raise ExecutorError("routing needs a settled public assessment")
            rigour = public["result"]["rigour"]
            control = controller_control.resolve(
                self.project, explicit_mode=explicit_mode,
                session_id=session_id, task_revision=rigour["task_revision"])
            expected = controller_policy.decide(
                rigour, control, selected_cell=value["ladder"][0],
                controller_profile=decision["controller_profile"],
                public_passed=decision["public_pass_observed"])
            if (decision != expected
                    or decision["remaining_budget"] != self._budget(root_id).remaining()):
                raise ExecutorError("routing decision differs from current public evidence, control or budget")
            if profile_selection is None:
                profile_selection = controller_profile_policy.choose(
                    remaining_usd=decision["remaining_budget"],
                    experimental_admission=value["admission"]["policy"] ==
                    EXPERIMENTAL_N3_POLICY,
                    requested_profile=None if decision["controller_profile"] == "standard"
                    else decision["controller_profile"],
                    follow_on_floor_usd=controller_dispatch.FOLLOW_ON_FLOOR_USD)
            selection = controller_profile_policy.validate(profile_selection)
            current_selection = controller_profile_policy.choose(
                remaining_usd=decision["remaining_budget"],
                experimental_admission=value["admission"]["policy"] ==
                EXPERIMENTAL_N3_POLICY,
                requested_profile=None if selection["source"] ==
                "automatic-retained" else selection["profile"],
                explicit_experimental=selection["source"] ==
                "explicit-experimental",
                follow_on_floor_usd=controller_dispatch.FOLLOW_ON_FLOOR_USD)
            if (selection["profile"] != decision["controller_profile"]
                    or selection != current_selection
                    or selection["remaining_usd_at_selection"] !=
                    decision["remaining_budget"]
                    or selection["experimental_admission"] !=
                    (value["admission"]["policy"] == EXPERIMENTAL_N3_POLICY)
                    or selection["follow_on_floor_usd"] !=
                    controller_dispatch.FOLLOW_ON_FLOOR_USD):
                raise ExecutorError("role-profile selection differs from frozen root")
            value["routing_decision"] = {
                "version": 2, "decision": decision,
                "decision_digest": digest(decision), "control": control.as_dict(),
                "profile_selection": selection}
            _event(value, "routing_decision_frozen",
                   decision_id=decision["decision_id"],
                   effective_action=decision["effective_action"],
                   control_revision=control.state_revision,
                   profile_policy=selection["policy_id"],
                   profile_source=selection["source"])
            _write(path, value)
        return self.status(root_id)

    def block_routing_decision(self, root_id: str, decision_id: str,
                               reason: str) -> dict:
        """Surface a frozen clarification, budget stop or Controller gap."""
        if not isinstance(reason, str) or not reason.strip():
            raise ExecutorError("blocked routing needs a reason")
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            routing = value.get("routing_decision")
            if (routing is None or routing["decision"]["decision_id"] != decision_id
                    or routing["decision"]["effective_action"] == "worker"):
                raise ExecutorError("blocked routing does not match the frozen decision")
            if value["state"] == "blocked":
                return self.status(root_id)
            if value["state"] != "ready":
                raise ExecutorError("root is no longer ready for routing resolution")
            value["block"] = {"reason": reason[:500], "resume_phase": None}
            _event(value, "routing_blocked", decision_id=decision_id,
                   reason=value["block"]["reason"])
            transition(value, "blocked", reason=value["block"]["reason"])
            _write(path, value)
        return self.status(root_id)

    def claim_controller(self, root_id: str, *, decision_id: str,
                         controller_task_revision: str,
                         problem_text: str, input_revision: dict,
                         acceptance_digest: str, maximum_usd: float,
                         minimum_usd: float, follow_on_floor_usd: float) -> dict:
        """Claim the single Controller intervention on this immutable root revision.

        The root journal is written before any budget start. A crash can leave
        a conservative pending claim, but cannot make the same revision appear
        unused. Worker dispatch remains closed until the later workflow bridge
        explicitly resolves this claim.
        """
        path = self._path(root_id)
        if (not isinstance(decision_id, str) or not ID.fullmatch(decision_id)
                or not isinstance(controller_task_revision, str)
                or not SHA256.fullmatch(controller_task_revision)):
            raise ExecutorError("Controller decision or task revision is invalid")
        try:
            if (dispatch_budget.units(minimum_usd) <= 0
                    or dispatch_budget.units(maximum_usd) < dispatch_budget.units(minimum_usd)
                    or dispatch_budget.units(follow_on_floor_usd) <= 0):
                raise ValueError("invalid Controller or worker allowance")
        except dispatch_budget.BudgetError as exc:
            raise ExecutorError("invalid Controller or worker allowance") from exc
        with route.ledger_lock(path):
            value = _read(path)
            definition = value["definition"]
            if (value["state"] != "ready" or value.get("controller_admission") is not None):
                raise ExecutorError("task revision is not ready for a first Controller admission")
            if value["admission"]["policy"] == PENDING_N3_POLICY:
                raise ExecutorError("worker selection is not frozen before Controller admission")
            routing = value.get("routing_decision")
            if routing is not None and (
                    routing["decision"]["effective_action"] != "controller"
                    or routing["decision"]["decision_id"] != decision_id):
                raise ExecutorError("Controller claim differs from frozen routing decision")
            if (value.get("public_assessment") is not None
                    and value["public_assessment"]["status"] != "settled"):
                raise ExecutorError("public assessment must be settled before Controller admission")
            if (definition["goal"] != problem_text
                    or definition["input_revision"] != input_revision
                    or definition["acceptance_definition"]["contract_digest"]
                    != acceptance_digest):
                raise ExecutorError("Controller inputs differ from the frozen N1 task definition")
            budget = self._budget(root_id)
            available = budget.remaining()
            cap = min(maximum_usd, available - follow_on_floor_usd)
            if cap < minimum_usd:
                raise ExecutorError("Controller would consume the reserved worker allowance")
            revision_id = value["revision"]["revision_id"]
            invocation_id = "controller-" + revision_id[:24]
            follow_on_id = "controller-follow-on-" + revision_id[:24]
            value["controller_admission"] = {
                "version": 2,
                "revision_id": revision_id, "decision_id": decision_id,
                "invocation_id": invocation_id,
                "follow_on_invocation_id": follow_on_id,
                "controller_task_revision": controller_task_revision,
                "allowance_usd": cap, "follow_on_floor_usd": follow_on_floor_usd,
                "status": "intent"}
            _event(value, "controller_admitted", decision_id=decision_id,
                   invocation_id=invocation_id, allowance_usd=cap)
            _write(path, value)
            try:
                # Hold the downstream worker/verification allowance in the
                # same root ledger. X4 must settle this unused hold before
                # atomically admitting the worker from the frozen handoff.
                budget.reserve(follow_on_id, follow_on_floor_usd,
                               follow_on_floor_usd,
                               {"revision_id": revision_id,
                                "allocation": "worker-verification-hold"})
                allowance = budget.reserve(invocation_id, cap, minimum_usd,
                                           {"decision_id": decision_id,
                                            "revision_id": revision_id,
                                            "allocation": "controller"})
                budget.start(invocation_id)
            except dispatch_budget.BudgetError as exc:
                raise ExecutorError("Controller claim is pending; reconcile the root budget") from exc
            value["controller_admission"]["allowance_usd"] = allowance
            value["controller_admission"]["status"] = "started"
            _event(value, "controller_started", invocation_id=invocation_id,
                   allowance_usd=allowance)
            _write(path, value)
            return {"root_id": root_id, "revision_id": revision_id,
                     "invocation_id": invocation_id, "allowance_usd": allowance,
                     "follow_on_invocation_id": follow_on_id,
                     "budget_path": str(budget.path)}

    def accept_controller_handoff(self, root_id: str, decision_id: str) -> dict:
        """Validate durable Controller evidence before releasing the worker hold.

        This is the only transition from a paid Controller invocation to N1
        worker execution. It rechecks the packet and budget after a restart;
        a dispatcher's success flag alone has no authority over the root.
        """
        import controller_dispatch  # Deferred: the dispatcher imports this module.

        path = self._path(root_id)
        if not isinstance(decision_id, str) or not ID.fullmatch(decision_id):
            raise ExecutorError("invalid Controller decision id")
        with route.ledger_lock(path):
            value = _read(path)
            admission = value.get("controller_admission")
            if admission is None or admission["decision_id"] != decision_id:
                raise ExecutorError("Controller decision does not own this task root")
            routing = value.get("routing_decision")
            if routing is not None and routing["decision"]["decision_id"] != decision_id:
                raise ExecutorError("Controller handoff differs from frozen routing decision")
            if value["state"] != "ready":
                raise ExecutorError("task root is no longer ready for Controller handoff")
            if admission["status"] == "worker-ready":
                return self.status(root_id)
            if admission["status"] != "started" or admission.get("version") != 2:
                raise ExecutorError("Controller invocation has not completed its root claim")

            dispatch_dir = self.project / controller_dispatch.ROOT_RELATIVE / decision_id
            state_path = dispatch_dir / "dispatch-state.json"
            handoff_path = dispatch_dir / "worker-handoff.json"
            if (dispatch_dir.is_symlink() or state_path.is_symlink()
                    or handoff_path.is_symlink()):
                raise ExecutorError("Controller dispatch path is redirected")
            try:
                if state_path.stat().st_size > 200_000 or handoff_path.stat().st_size > 20_000:
                    raise ValueError("Controller dispatch state exceeds size bound")
                state = json.loads(state_path.read_text(encoding="utf-8"))
                decision = controller_dispatch._validate_decision(state["decision"])
                result = state["controller_result"]
                before = state["source_digest_before"]
                if (state["stage"] != "worker-ready"
                        or state["root_task_id"] != root_id
                        or state["root_revision_id"] != admission["revision_id"]
                        or state["controller_invocations"] != 1
                        or state["invocation_id"] != admission["invocation_id"]
                        or decision["decision_id"] != decision_id
                        or decision["task_revision"] != admission["controller_task_revision"]
                        or decision["effective_action"] != "controller"
                        or decision["selected_cell"] != value["ladder"][0]
                        or not isinstance(before, str) or not SHA256.fullmatch(before)
                        or not isinstance(result, dict)
                        or not result.get("terminal")
                        or not result.get("accounting_complete")
                        or result.get("cost_usd") is None):
                    raise ValueError("Controller dispatch does not match the frozen root")
                frozen = value["definition"]
                request = controller_dispatch.ControllerRequest(
                    self.project, frozen["goal"],
                    {"contract_digest": frozen["acceptance_definition"]["contract_digest"]},
                    admission["allowance_usd"], decision_id,
                    admission["controller_task_revision"], frozen["input_revision"],
                    controller_profile=decision["controller_profile"])
                packet, run_dir = controller_dispatch._validated_packet(result, request, before)
                packet_path = run_dir / "controller-evidence.json"
                if packet_path.is_symlink() or packet_path.stat().st_size > 200_000:
                    raise ValueError("Controller evidence file is redirected or unbounded")
                if json.loads(packet_path.read_text(encoding="utf-8")) != packet:
                    raise ValueError("Controller evidence file differs from settled packet")
                relative_packet = packet_path.relative_to(self.project).as_posix()
                handoff = controller_dispatch._worker_handoff(decision, packet, relative_packet)
                if (state["worker_handoff"] != handoff
                        or json.loads(handoff_path.read_text(encoding="utf-8")) != handoff):
                    raise ValueError("Controller handoff differs from validated evidence")
                budget = self._budget(root_id)
                snapshot = budget.snapshot()
                controller_row = snapshot["invocations"][admission["invocation_id"]]
                hold_id = admission["follow_on_invocation_id"]
                hold_row = snapshot["invocations"][hold_id]
                if (snapshot["cancelled"] or snapshot["breached"]
                        or controller_row["state"] != "settled"
                        or controller_row["cost_usd"] != result["cost_usd"]
                        or controller_row["resolution"]["evidence"] != "controller-adapter-result"
                        or (set(snapshot["unresolved"]) - {hold_id})
                        or (hold_row["state"] == "settled"
                            and (hold_row["cost_usd"] != 0
                                 or hold_row["resolution"]["evidence"] !=
                                 "controller-validated-worker-handoff"))
                        or hold_row["state"] not in {"reserved", "settled"}):
                    raise ValueError("root budget does not match a settled Controller and worker hold")
                if hold_row["state"] == "reserved":
                    budget.settle(hold_id, 0.0, final=True, telemetry={},
                                  evidence="controller-validated-worker-handoff")
            except (OSError, ValueError, KeyError, TypeError,
                    controller_dispatch.DispatchError, dispatch_budget.BudgetError) as exc:
                raise ExecutorError(f"Controller handoff rejected: {exc}") from exc
            admission["status"] = "worker-ready"
            admission["handoff"] = handoff
            admission["handoff_digest"] = digest(handoff)
            _event(value, "controller_handoff_validated",
                   handoff_digest=admission["handoff_digest"])
            _write(path, value)
        return self.status(root_id)

    def override_cell(self, root_id: str, *, cell: str, actor: str, reason: str) -> None:
        """B0 dispatch never silently changes identity; use shadow_select."""
        self.status(root_id)  # Validate the root before reporting an unsupported request.
        raise ExecutorError("cell overrides are unsupported in N1; use shadow_select for N3 candidates")

    def shadow_select(self, root_id: str, assessment: dict,
                      *, override: dict | None = None) -> dict:
        """Journal a candidate for the next attempt without changing B0.

        A decision made during a running invocation belongs to the following
        attempt. It cannot relabel that invocation, amend a budget, or promote
        the experimental selector to dispatch authority.
        """
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            if value["admission"]["policy"] != "B0":
                raise ExecutorError("shadow selection is only available on B0 roots")
            if value["state"] in TERMINAL or value["state"] in {"uncertain", "cancelled"}:
                raise ExecutorError("shadow selection needs a live, certain root")
            next_sequence = len(value["attempts"]) + 1
            if next_sequence > len(value["ladder"]):
                raise ExecutorError("no future attempt remains")
            capability = self.adapter.capability(self.project)
            if digest(capability) != value["admission"]["capability_digest"]:
                raise ExecutorError("host capability changed since admission")
            if override is not None:
                authority = override.get("authority_id") if isinstance(override, dict) else None
                if authority in {item.get("override", {}).get("authority_id")
                                 for item in value.get("shadow_decisions", [])
                                 if item.get("override") is not None}:
                    raise ExecutorError("override authority already used")
            budget = self._budget(root_id)
            decision = worker_selector.select(
                assessment,
                supported_cells=set(capability.get("supported_cells", [])),
                remaining_usd=budget.remaining(),
                budget_enforced=capability.get("budget_enforced") is True,
                override=override)
            row = {"sequence": next_sequence, "decision": decision,
                   "decision_digest": digest(decision),
                   "b0_cell": value["ladder"][next_sequence - 1],
                   "override": decision["override"],
                   "recorded_at": acceptance.utc_now()}
            value.setdefault("shadow_decisions", []).append(row)
            _event(value, "shadow_selection", sequence=next_sequence,
                   decision_digest=row["decision_digest"],
                   selected_cell=decision["selected_cell"],
                   b0_cell=row["b0_cell"], override_authority=(
                       override.get("authority_id") if override else None))
            _write(path, value)
            return row

    def admit(self, *, goal: str, scope: list[str], permissions: list[str],
              acceptance_path: Path, budget_usd: float, authority_id: str,
              actor: str, root_id: str | None = None, task_id: str | None = None,
              axes: tuple[str, str, str] = ("structured", "medium", "contained"),
              input_paths: list[str] | None = None,
              deadline_at: str | None = None,
              experimental_dispatch: dict | None = None) -> str:
        root_id = root_id or secrets.token_hex(12)
        task_id = task_id or root_id
        if not all(isinstance(x, str) and ID.fullmatch(x) for x in (root_id, task_id, authority_id)):
            raise ExecutorError("root, task and authority ids must be safe opaque identifiers")
        if not actor.strip() or not goal.strip() or len(goal) > 20_000 or not scope:
            raise ExecutorError("actor, bounded goal and write scope are required")
        if deadline_at is not None:
            try:
                deadline = dt.datetime.fromisoformat(deadline_at.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ExecutorError("deadline must be an ISO timestamp") from exc
            if deadline.tzinfo is None:
                raise ExecutorError("deadline must include a timezone")
        paths = [acceptance._relative(self.project, raw)[0] for raw in scope]
        inputs = [acceptance._relative(self.project, raw)[0] for raw in (input_paths or [])]
        if _overlap(inputs, paths):
            raise ExecutorError("frozen input paths cannot overlap worker write scope")
        input_snapshot = acceptance.snapshot(self.project, inputs)
        if input_snapshot["missing"]:
            raise ExecutorError(f"frozen inputs are missing: {input_snapshot['missing']}")
        if any(p == ".claude" or p.startswith(".claude/") for p in paths):
            raise ExecutorError("worker scope cannot include executor state")
        if permissions != ["read", "edit"]:
            raise ExecutorError("N1 supports only read/edit permissions")
        frozen = acceptance.load_contract(self.project, acceptance_path)
        capability = self.adapter.capability(self.project)
        _declared_worker_call_cap(capability)
        plan = route.plan(*axes)
        if plan["policy"] != "B0" or plan["controller"] is not None or len(plan["execution_ladder"]) != 3:
            raise ExecutorError("qualified B0 policy unavailable")
        ladder = plan["execution_ladder"]
        experimental = None
        if experimental_dispatch is not None:
            experimental = _experimental_policy(experimental_dispatch, capability,
                                                budget_usd, self.adapter, ladder)
            ladder = experimental["ladder"]
        cells = [model_registry.resolve_cell(cell) for cell in ladder]
        if any(not cell["direct_worker"] for cell in cells):
            raise ExecutorError("B0 contains an unavailable direct worker cell")
        root_path = self._path(root_id)
        with route.ledger_lock(self.registry):
            if self.registry.exists():
                registry = _read_registry(self.registry)
            else:
                registry = {"schema_version": 2, "authorities": {}, "roots": {}}
            if authority_id in registry["authorities"]:
                raise ExecutorError("root-creation authority already used")
            if root_path.exists() or root_id in registry["roots"]:
                raise ExecutorError("root id already exists")
            for prior in registry["roots"].values():
                if prior["active"] and _overlap(paths, prior["scope"]):
                    raise ExecutorError("conflicting project writer scope")
            project_id_path = self.base / "project-id"
            if project_id_path.exists():
                project_id = project_id_path.read_text(encoding="utf-8").strip()
            else:
                project_id = secrets.token_hex(16)
                route._atomic_write_bytes(project_id_path, (project_id + "\n").encode())
            definition = _definition(project_id, root_id, task_id, goal, paths,
                                     permissions,
                                      {"git": acceptance.revision(self.project),
                                       "input_paths": inputs,
                                      "content": input_snapshot}, frozen)
            definition_digest = digest(definition)
            revision = {"revision_number": 1, "parent_revision_id": None,
                        "definition_digest": definition_digest, "change_reason": "initial",
                        "authority_id": authority_id}
            revision["revision_id"] = digest({**revision, "task_id": task_id})
            value = {"schema_version": 2, "record_type": "TaskRoot", "root_id": root_id,
                     "task_id": task_id, "state": "prepared", "definition": definition,
                     "definition_digest": definition_digest, "revision": revision,
                     "admission": {"actor": actor, "authority_id": authority_id,
                                   "capability_digest": digest(capability),
                                   "policy": (experimental["policy"] if experimental else "B0"),
                                   "policy_digest": (digest(experimental) if experimental else digest(ladder)),
                                   "campaign_prompt_digest": (digest(self.campaign_prompt)
                                                              if self.campaign_prompt else None),
                                   "deadline_at": deadline_at},
                     "ladder": ladder, "axes": axes, "attempts": [], "journal": [],
                     "owner_generation": 0, "decision_generation": 0,
                     "block": None, "created_at": acceptance.utc_now()}
            if experimental is not None:
                value["experimental_policy"] = experimental
            _event(value, "root_admitted", authority_id=authority_id,
                   definition_digest=definition_digest)
            transition(value, "ready")
            self._budget(root_id, budget_usd)
            _write(root_path, value)
            registry["authorities"][authority_id] = root_id
            registry["roots"][root_id] = {"scope": paths, "active": True,
                                          "task_id": task_id}
            _write_registry(self.registry, registry)
        return root_id

    def _release_claim(self, root_id: str) -> None:
        # Called only after a terminal task with no unresolved writer/hold.
        with route.ledger_lock(self.registry):
            registry = _read_registry(self.registry)
            if root_id in registry["roots"]:
                registry["roots"][root_id]["active"] = False
                _write_registry(self.registry, registry)

    def run(self, root_id: str, *, stop_after_attempts: int | None = None) -> dict:
        """Drive the frozen ladder until accepted, exhausted or stopped.

        A surviving `running` intent is never relaunched. The lock is released
        while a worker or verifier runs; callback generation is checked before
        committing its receipt. An optional attempt ceiling returns at a
        verified, settled public failure before dispatching the next cell.
        """
        if stop_after_attempts is not None and (
                type(stop_after_attempts) is not int or stop_after_attempts < 1):
            raise ExecutorError("stop_after_attempts must be a positive integer")
        path = self._path(root_id)
        budget = self._budget(root_id)
        while True:
            with route.ledger_lock(path):
                value = _read(path)
                if value["state"] in TERMINAL:
                    return self.status(root_id)
                if value.get("delegation") and value["delegation"]["state"] != "complete":
                    raise ExecutorError("managed children must be reconciled before root B0 dispatch")
                deadline_at = value["admission"].get("deadline_at")
                if deadline_at and dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(deadline_at.replace("Z", "+00:00")):
                    _settle_persisted_receipt(value, budget)
                    _release_controller_hold(value, budget,
                                             "deadline-before-controller-worker-handoff")
                    value["owner_generation"] += 1
                    _event(value, "deadline", deadline_at=deadline_at)
                    transition(value, "cancelled", reason="deadline exceeded")
                    budget.cancel()
                    _write(path, value)
                    return self.status(root_id)
                if (stop_after_attempts is not None and value["state"] == "ready"
                        and len(value["attempts"]) >= stop_after_attempts):
                    attempt = value["attempts"][-1]
                    receipt = attempt.get("receipt")
                    verification = attempt.get("verification")
                    if (attempt.get("process_state") != "terminal"
                            or not isinstance(receipt, dict)
                            or not _valid_receipt(attempt, receipt)
                            or not isinstance(verification, dict)
                            or verification.get("status") != "fail"
                            or not acceptance.qualified(verification)
                            or budget.snapshot()["unresolved"]):
                        raise ExecutorError("attempt checkpoint is not a settled public failure")
                    return self.status(root_id)
                controller = value.get("controller_admission")
                public_assessment = value.get("public_assessment")
                if value["admission"]["policy"] == PENDING_N3_POLICY:
                    raise ExecutorError("worker selection is not frozen before dispatch")
                routing = value.get("routing_decision")
                if routing is not None:
                    action = routing["decision"]["effective_action"]
                    if action == "controller" and (
                            controller is None or controller["status"] != "worker-ready"):
                        raise ExecutorError("frozen Controller decision requires a validated handoff")
                    if action in {"blocked", "clarify"}:
                        raise ExecutorError("frozen routing decision requires operator resolution")
                    if action == "worker" and controller is not None:
                        raise ExecutorError("worker decision conflicts with Controller admission")
                if (public_assessment is not None
                        and public_assessment["status"] != "settled"):
                    raise ExecutorError("resolve public assessment accounting before worker dispatch")
                if controller is not None and controller["status"] != "worker-ready":
                    raise ExecutorError(
                        "Controller admission is owned by the task revision; "
                        "resolve its handoff before worker dispatch")
                if value["state"] in {"blocked", "awaiting_review", "uncertain"}:
                    return self.status(root_id)
                if value["state"] == "running":
                    attempt = value["attempts"][-1]
                    receipt = attempt.get("receipt")
                    if receipt is not None:
                        # Receipt was durably recorded, but the process died
                        # before budget settlement or task transition.
                        if receipt.get("terminal") and receipt.get("writer_stopped") and receipt.get("cost_usd") is not None:
                            budget.settle(attempt["invocation_id"], receipt["cost_usd"], final=True,
                                          telemetry=receipt.get("usage") or {},
                                          evidence=f"receipt:{attempt['receipt_digest']}")
                            attempt["process_state"] = "terminal"
                            _event(value, "recovered_settlement", invocation_id=attempt["invocation_id"])
                            if _valid_receipt(attempt, receipt):
                                transition(value, "verifying")
                            else:
                                value["block"] = {"reason": "post-dispatch identity or process fault",
                                                  "resume_phase": None}
                                transition(value, "blocked", reason=value["block"]["reason"])
                        else:
                            attempt["process_state"] = "uncertain"
                            transition(value, "uncertain", reason="incomplete receipt")
                    else:
                        attempt["process_state"] = "uncertain"
                        transition(value, "uncertain", reason="intent without committed receipt")
                    _write(path, value)
                    if value["state"] != "verifying":
                        return self.status(root_id)
                if value["state"] == "admitted":
                    attempt = value["attempts"][-1]
                    row = budget.snapshot()["invocations"].get(attempt["invocation_id"])
                    if row and row["state"] == "reserved":
                        budget.settle(attempt["invocation_id"], 0.0, final=True,
                                      telemetry={}, evidence="local:pre-dispatch-no-intent")
                        _event(value, "unused_reservation_released", invocation_id=attempt["invocation_id"])
                        value.setdefault("abandoned_operations", []).append(attempt)
                        value["attempts"].pop()
                        transition(value, "blocked", reason="pre-dispatch recovery; explicit resume required")
                        value["block"] = {"reason": "pre-dispatch recovery", "resume_phase": "ready"}
                    else:
                        transition(value, "uncertain", reason="budget start may have reached host")
                    _write(path, value)
                    return self.status(root_id)
                if value["state"] == "verifying":
                    attempt = value["attempts"][-1]
                    generation = value["owner_generation"]
                    request = None
                else:
                    if len(value["attempts"]) >= len(value["ladder"]):
                        raise ExecutorError("attempt ceiling reached outside verifier")
                    if value["state"] != "ready":
                        raise ExecutorError(f"cannot dispatch from {value['state']}")
                    if value["attempts"] and value["attempts"][-1]["process_state"] == "reserved":
                        orphan = value["attempts"][-1]
                        row = budget.snapshot()["invocations"].get(orphan["invocation_id"])
                        if row is not None:
                            if row["state"] != "reserved":
                                transition(value, "blocked", reason="orphan decision with started invocation")
                                value["block"] = {"reason": "orphan decision with started invocation",
                                                  "resume_phase": "ready"}
                                _write(path, value)
                                return self.status(root_id)
                            budget.settle(orphan["invocation_id"], 0.0, final=True,
                                          telemetry={}, evidence="local:decision-before-admission")
                        value.setdefault("abandoned_operations", []).append(orphan)
                        value["attempts"].pop()
                        _event(value, "recovered_pre_dispatch_decision",
                               invocation_id=orphan["invocation_id"], budget_row_present=row is not None)
                        _write(path, value)
                    try:
                        if value["admission"].get("campaign_prompt_digest") != (
                                digest(self.campaign_prompt) if self.campaign_prompt else None):
                            raise ExecutorError("campaign prompt changed since admission")
                        input_revision = value["definition"]["input_revision"]
                        if acceptance.snapshot(self.project, input_revision["input_paths"])["digest"] != input_revision["content"]["digest"]:
                            raise ExecutorError("frozen task inputs changed before dispatch")
                        capability = self.adapter.capability(self.project)
                        if digest(capability) != value["admission"]["capability_digest"]:
                            raise ExecutorError("host capability changed since admission")
                        worker_call_cap = _declared_worker_call_cap(capability)
                    except Exception as exc:
                        value["block"] = {"reason": str(exc), "resume_phase": "ready"}
                        transition(value, "blocked", reason=str(exc))
                        _write(path, value)
                        return self.status(root_id)
                    sequence = len(value["attempts"]) + 1
                    cell = value["ladder"][sequence - 1]
                    call_allowance = min(budget.remaining(), worker_call_cap) if (
                        worker_call_cap is not None) else budget.remaining()
                    if value["admission"]["policy"] in EXPERIMENTAL_POLICIES:
                        projection = model_registry.projected_cost(cell)
                        if (projection["known"] and
                                projection["cost_per_run_usd"] > call_allowance):
                            value["block"] = {"reason": "projected experimental call exceeds remaining budget",
                                              "resume_phase": "ready"}
                            transition(value, "blocked", reason=value["block"]["reason"])
                            _write(path, value)
                            return self.status(root_id)
                    invocation = secrets.token_hex(16)
                    token = secrets.token_hex(24)
                    decision = {"revision_id": value["revision"]["revision_id"],
                                "sequence": sequence,
                                "policy": value["admission"]["policy"], "cell": cell,
                                "cell_resolution": model_registry.resolve_cell(cell),
                                "generation": value["decision_generation"] + 1}
                    if controller is not None:
                        decision["controller_handoff_digest"] = controller["handoff_digest"]
                    if value["admission"]["policy"] in EXPERIMENTAL_POLICIES:
                        policy = value["experimental_policy"]
                        decision.update(policy_digest=value["admission"]["policy_digest"],
                                        arm=policy["arm"],
                                        manifest_sha256=policy["manifest_sha256"],
                                        assessment_digest=policy["assessment_digest"],
                                        eligible_cells=policy["eligible_cells"],
                                        cost_ceiling_usd=policy["cost_ceiling_usd"])
                    decision_digest = digest(decision)
                    attempt = {"schema_version": 2, "record_type": "AttemptResult",
                               "sequence": sequence, "reason": ("fixed_floor", "one_local_repair", "fixed_fallback")[sequence-1],
                               "invocation_id": invocation, "admission_token": token,
                               "revision_id": value["revision"]["revision_id"],
                               "decision_digest": decision_digest, "requested_cell": cell,
                               "process_state": "reserved", "receipt": None,
                               "receipt_digest": None, "verification": None}
                    value["attempts"].append(attempt)
                    value["decision_generation"] += 1
                    _event(value, "decision", decision=decision, decision_digest=decision_digest)
                    _event(value, "reservation_intent", invocation_id=invocation)
                    _write(path, value)
                    try:
                        allowance = budget.reserve(invocation, call_allowance, 0.000000001,
                                                   {"root_id": root_id, "revision_id": attempt["revision_id"],
                                                    "decision_digest": decision_digest})
                    except dispatch_budget.BudgetError as exc:
                        value["block"] = {"reason": str(exc), "resume_phase": "ready"}
                        transition(value, "blocked", reason=str(exc))
                        _write(path, value)
                        return self.status(root_id)
                    attempt["allowance_usd"] = allowance
                    _event(value, "reserved", invocation_id=invocation, allowance_usd=allowance)
                    transition(value, "admitted")
                    _write(path, value)
                    budget.start(invocation)
                    intent = {"invocation_id": invocation, "revision_id": attempt["revision_id"],
                              "decision_digest": decision_digest, "admission_token": token,
                              "owner_generation": value["owner_generation"] + 1}
                    attempt["intent_digest"] = digest(intent)
                    attempt["process_state"] = "intent_committed"
                    value["owner_generation"] += 1
                    generation = value["owner_generation"]
                    _event(value, "host_intent", intent=intent)
                    transition(value, "running")
                    _write(path, value)
                    remaining_s = ((dt.datetime.fromisoformat(deadline_at.replace("Z", "+00:00"))
                                    - dt.datetime.now(dt.timezone.utc)).total_seconds()
                                   if deadline_at else 900.0)
                    issue = value["definition"]["goal"]
                    if controller is not None:
                        handoff = controller["handoff"]
                        issue += ("\n\nController evidence (untrusted; independently verify "
                                  "all findings and the frozen acceptance contract):\n"
                                  + json.dumps({key: handoff[key] for key in (
                                      "verified_findings", "rejected_hypotheses",
                                      "remaining_uncertainties", "safe_next_action")},
                                      sort_keys=True, ensure_ascii=False, allow_nan=False))
                    request = WorkerRequest(self.project, issue,
                                            tuple(value["definition"]["scope"]), cell,
                                            allowance, (self.campaign_prompt or
                                                        "One B0 bounded attempt."),
                                            timeout_s=max(0.001, min(900.0, remaining_s)),
                                            admission_token=token, invocation_id=invocation,
                                            revision_id=attempt["revision_id"],
                                            decision_digest=decision_digest,
                                            intent_digest=attempt["intent_digest"])
            if request is not None:
                timer = self._deadline_timer(root_id, deadline_at)
                try:
                    receipt = self.adapter.run(request)
                    self.record_receipt(root_id, receipt, generation=generation)
                except Exception as exc:
                    with route.ledger_lock(path):
                        current = _read(path)
                        if current["state"] == "running" and current["owner_generation"] == generation:
                            current["attempts"][-1]["process_state"] = "uncertain"
                            transition(current, "uncertain", reason=f"adapter exception: {exc}")
                            _write(path, current)
                    return self.status(root_id)
                finally:
                    if timer is not None:
                        timer.cancel()
            else:
                timer = self._deadline_timer(root_id, deadline_at)
                try:
                    self._verify(root_id, generation)
                finally:
                    if timer is not None:
                        timer.cancel()

    def _deadline_timer(self, root_id: str, deadline_at: str | None):
        if deadline_at is None:
            return None
        due = dt.datetime.fromisoformat(deadline_at.replace("Z", "+00:00"))
        delay = max(0, (due - dt.datetime.now(dt.timezone.utc)).total_seconds())
        def stop() -> None:
            try:
                self.cancel(root_id, actor="deadline", reason="deadline exceeded")
            except (ExecutorError, dispatch_budget.BudgetError):
                pass
        timer = threading.Timer(delay, stop)
        timer.daemon = True
        timer.start()
        return timer

    def record_receipt(self, root_id: str, receipt: dict, *, generation: int) -> None:
        path = self._path(root_id)
        budget = self._budget(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            attempt = next((x for x in value["attempts"] if x["invocation_id"] == receipt.get("invocation_id")), None)
            if attempt is None:
                raise ExecutorError("receipt has no admitted invocation")
            receipt_digest = digest(receipt)
            late = attempt.get("late_receipts") or []
            if any(row["receipt_digest"] == receipt_digest for row in late):
                return
            if late:
                _event(value, "conflicting_late_receipt", invocation_id=attempt["invocation_id"],
                       conflicting_digest=receipt_digest, conflicting_receipt=receipt)
                _write(path, value)
                raise ExecutorError("conflicting late receipt retained for reconciliation")
            if attempt["receipt_digest"]:
                if attempt["receipt_digest"] == receipt_digest:
                    return
                _event(value, "conflicting_receipt", invocation_id=attempt["invocation_id"],
                       conflicting_digest=receipt_digest, conflicting_receipt=receipt)
                _write(path, value)
                raise ExecutorError("conflicting receipt retained for reconciliation")
            if any(receipt.get(key) != expected for key, expected in {
                    "admission_token": attempt["admission_token"],
                    "revision_id": attempt["revision_id"],
                    "decision_digest": attempt["decision_digest"],
                    "intent_digest": attempt.get("intent_digest"),
                    "requested_cell": attempt["requested_cell"]}.items()):
                _event(value, "unmatched_receipt", invocation_id=attempt["invocation_id"],
                       receipt_digest=receipt_digest, receipt=receipt)
                if value["state"] == "running":
                    value["block"] = {"reason": "receipt identity mismatch; hold retained",
                                      "resume_phase": None}
                    transition(value, "blocked", reason=value["block"]["reason"])
                _write(path, value)
                raise ExecutorError("receipt identity does not match admission")
            if value["owner_generation"] != generation or value["state"] != "running":
                attempt.setdefault("late_receipts", []).append(
                    {"generation": generation, "receipt_digest": receipt_digest,
                     "receipt": receipt})
                if receipt.get("terminal") and receipt.get("writer_stopped") and receipt.get("cost_usd") is not None:
                    budget.settle(attempt["invocation_id"], receipt["cost_usd"], final=True,
                                  telemetry=receipt.get("usage") or {}, evidence=f"late-receipt:{receipt_digest}")
                    attempt["process_state"] = "terminal"
                else:
                    attempt["process_state"] = "uncertain"
                _event(value, "late_receipt", invocation_id=attempt["invocation_id"],
                       generation=generation, receipt_digest=receipt_digest)
                _write(path, value)
                return
            attempt["receipt"] = receipt
            attempt["receipt_digest"] = receipt_digest
            _event(value, "receipt", invocation_id=attempt["invocation_id"], receipt_digest=receipt_digest)
            # Persist the raw receipt before the independent budget settlement.
            _write(path, value)
            if receipt.get("terminal") and receipt.get("writer_stopped") and receipt.get("cost_usd") is not None:
                budget.settle(attempt["invocation_id"], receipt["cost_usd"], final=True,
                              telemetry=receipt.get("usage") or {}, evidence=f"receipt:{receipt_digest}")
                attempt["process_state"] = "terminal"
                _event(value, "settled", invocation_id=attempt["invocation_id"])
            else:
                attempt["process_state"] = "uncertain"
            if attempt["process_state"] == "uncertain":
                transition(value, "uncertain", reason="incomplete cost or writer termination")
            elif not _valid_receipt(attempt, receipt):
                value["block"] = {"reason": "post-dispatch identity or process fault", "resume_phase": None}
                transition(value, "blocked", reason=value["block"]["reason"])
            else:
                transition(value, "verifying")
            _write(path, value)

    def reconcile_uncertain(self, root_id: str, *, actor: str, reason: str,
                            cost_usd: float, evidence: str,
                            writers_stopped: bool) -> dict:
        """Close an ambiguous charge without replaying its worker invocation."""
        if not actor.strip() or not reason.strip() or not evidence.strip() or writers_stopped is not True:
            raise ExecutorError("uncertainty resolution needs actor, reason, evidence and stopped-writer proof")
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] != "uncertain":
                raise ExecutorError("task is not uncertain")
            attempt = value["attempts"][-1]
            budget = self._budget(root_id)
            budget_row = budget.snapshot()["invocations"][attempt["invocation_id"]]
            if budget_row["state"] == "settled":
                if budget_row["cost_usd"] != cost_usd:
                    raise ExecutorError("reconciliation cost conflicts with settled charge")
            else:
                budget.settle(attempt["invocation_id"], cost_usd,
                              final=True, telemetry={"reconciled_by": actor},
                              evidence=evidence)
            attempt["process_state"] = "terminal"
            attempt.setdefault("reconciliations", []).append(
                {"actor": actor, "reason": reason, "evidence": evidence,
                 "cost_usd": cost_usd, "writers_stopped": True})
            _event(value, "uncertainty_reconciled", invocation_id=attempt["invocation_id"],
                   actor=actor, evidence=evidence, cost_usd=cost_usd)
            late = attempt.get("late_receipts") or []
            receipt = attempt.get("receipt") or (late[-1]["receipt"] if late else {})
            if _valid_receipt(attempt, receipt):
                transition(value, "verifying", reason="operator reconciled receipt")
            else:
                value["block"] = {"reason": "no validated completed receipt", "resume_phase": None}
                transition(value, "blocked", reason=value["block"]["reason"])
            _write(path, value)
        return self.status(root_id)

    def _verify(self, root_id: str, generation: int) -> None:
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] != "verifying" or value["owner_generation"] != generation:
                return
            attempt = value["attempts"][-1]
            frozen = value["definition"]["acceptance_definition"]
            acceptance_state = {**frozen, "status": "pending", "evidence": None, "review": None}
            entry_id = f"{root_id}-{attempt['sequence']}-{value['revision']['revision_number']}"
        try:
            if self.command_runner is None:
                result = acceptance.verify(self.project, acceptance_state, entry_id)
            else:
                result = acceptance.verify(self.project, acceptance_state, entry_id,
                                           command_runner=self.command_runner)
            artefact_copy = self._snapshot_artefacts(root_id, entry_id, result)
        except Exception as exc:
            with route.ledger_lock(path):
                value = _read(path)
                if value["state"] == "verifying" and value["owner_generation"] == generation:
                    value["block"] = {"reason": f"verifier error: {exc}", "resume_phase": "verifying"}
                    transition(value, "blocked", reason=value["block"]["reason"])
                    _write(path, value)
            return
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] != "verifying" or value["owner_generation"] != generation:
                _event(value, "late_verification", entry_id=entry_id, result_digest=digest(result))
                _write(path, value)
                return
            attempt = value["attempts"][-1]
            attempt["verification"] = result
            attempt["artefact_snapshot"] = artefact_copy
            _event(value, "verified", entry_id=entry_id, status=result["status"])
            if result["status"] == "pass" and acceptance.qualified(result):
                if _children_intact(self.project, value.get("delegation")):
                    transition(value, "accepted")
                else:
                    value["block"] = {"reason": "required child output changed before root acceptance",
                                      "resume_phase": "verifying"}
                    transition(value, "blocked", reason=value["block"]["reason"])
            elif result["status"] == "review_required":
                transition(value, "awaiting_review")
            elif result["status"] == "blocked":
                value["block"] = {"reason": "verifier blocked", "resume_phase": "verifying"}
                transition(value, "blocked", reason="verifier blocked")
            elif not result["evidence"]["protected_unchanged"]:
                value["block"] = {"reason": "protected path changed", "resume_phase": "verifying"}
                transition(value, "blocked", reason="protected path changed")
            elif result["status"] == "fail" and acceptance.qualified(result):
                transition(value, "ready" if len(value["attempts"]) < len(value["ladder"]) else "failed")
            else:
                value["block"] = {"reason": "unqualified verification", "resume_phase": "verifying"}
                transition(value, "blocked", reason="unqualified verification")
            _write(path, value)
        if value["state"] in TERMINAL and not self._budget(root_id).snapshot()["unresolved"]:
            self._release_claim(root_id)

    def _snapshot_artefacts(self, root_id: str, entry_id: str, result: dict) -> dict:
        """Retain exact worker output before a later B0 attempt can replace it."""
        entries = (result.get("evidence") or {}).get("artefacts", {}).get("files", [])
        saved: list[dict] = []
        for row in entries:
            relative = row["path"]
            if relative.endswith("/"):
                continue
            source = (self.project / relative).resolve(strict=True)
            if not source.is_relative_to(self.project):
                raise ExecutorError("artefact escaped actor root before snapshot")
            content = source.read_bytes()
            actual = hashlib.sha256(content).hexdigest()
            if actual != row["sha256"]:
                raise ExecutorError(f"artefact changed during verification: {relative}")
            target = self.base / root_id / "artefacts" / entry_id / relative
            route._atomic_write_bytes(target, content)
            saved.append({"path": target.relative_to(self.project).as_posix(),
                          "sha256": actual, "size": len(content)})
        return {"files": saved, "missing": (result.get("evidence") or {}).get("artefacts", {}).get("missing", []),
                "digest": digest(saved)}

    def review(self, root_id: str, *, decision: str, reviewer: str, notes: str = "") -> dict:
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] != "awaiting_review":
                raise ExecutorError("no rubric review is pending")
            attempt = value["attempts"][-1]
            entry_id = f"{root_id}-{attempt['sequence']}-{value['revision']['revision_number']}"
            current = acceptance.snapshot(self.project, attempt["verification"]["contract"]["required_outputs"])
            pending = attempt["verification"]["evidence"]["artefacts"]
            if current["digest"] != pending["digest"]:
                value["block"] = {"reason": "rubric artefacts changed before review",
                                  "resume_phase": "verifying"}
                transition(value, "blocked", reason=value["block"]["reason"])
                _write(path, value)
                return self.status(root_id)
            resolved = acceptance.review(self.project, attempt["verification"], entry_id,
                                         decision, reviewer, notes)
            attempt["verification"] = resolved
            _event(value, "human_review", entry_id=entry_id, status=resolved["status"], reviewer=reviewer)
            transition(value, "verifying")
            if resolved["status"] == "pass" and acceptance.qualified(resolved):
                if _children_intact(self.project, value.get("delegation")):
                    transition(value, "accepted")
                else:
                    value["block"] = {"reason": "required child output changed before root review",
                                      "resume_phase": "verifying"}
                    transition(value, "blocked", reason=value["block"]["reason"])
            elif resolved["review"]["protected"]["digest"] != resolved["protected_baseline"]["digest"]:
                value["block"] = {"reason": "protected path changed during review", "resume_phase": "verifying"}
                transition(value, "blocked", reason=value["block"]["reason"])
            elif resolved["status"] == "fail" and acceptance.qualified(resolved):
                transition(value, "ready" if len(value["attempts"]) < 3 else "failed")
            else:
                value["block"] = {"reason": "review evidence invalid", "resume_phase": "verifying"}
                transition(value, "blocked", reason="review evidence invalid")
            _write(path, value)
        if value["state"] in TERMINAL:
            self._release_claim(root_id)
        return self.status(root_id)

    def cancel(self, root_id: str, *, actor: str, reason: str) -> dict:
        if not isinstance(actor, str) or not actor.strip() or not isinstance(reason, str) or not reason.strip():
            raise ExecutorError("cancellation requires actor and reason")
        path = self._path(root_id)
        child_signals: list[str] = []
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] in TERMINAL:
                return self.status(root_id)
            _settle_persisted_receipt(value, self._budget(root_id))
            if value.get("delegation") and value["delegation"]["state"] != "complete":
                from managed_delegation import cancel_locked
                child_signals = cancel_locked(self, value, self._budget(root_id), actor, reason)
            _release_controller_hold(value, self._budget(root_id),
                                     "root-cancelled-before-worker-handoff")
            value["owner_generation"] += 1
            _event(value, "cancel_requested", actor=actor, reason=reason)
            transition(value, "cancelled", reason=reason)
            self._budget(root_id).cancel()
            _write(path, value)
        signal = getattr(self.adapter, "cancel", None)
        if callable(signal):
            for invocation_id in child_signals:
                signal(invocation_id)
        if value["attempts"] and value["attempts"][-1]["process_state"] == "intent_committed":
            if callable(signal):
                signal(value["attempts"][-1]["invocation_id"])
        return self.status(root_id)

    def continue_task(self, root_id: str, *, actor: str, authority_id: str,
                      reason: str, acceptance_path: Path | None = None) -> dict:
        """Create a linked revision after a safely settled cancelled task."""
        path = self._path(root_id)
        if not actor.strip() or not authority_id.strip() or not reason.strip():
            raise ExecutorError("continuation needs actor, authority and reason")
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] != "cancelled":
                raise ExecutorError("only a cancelled terminal task can continue")
            budget = self._budget(root_id)
            if budget.snapshot()["unresolved"] or any(
                    a["process_state"] in {"intent_committed", "uncertain"} for a in value["attempts"]):
                raise ExecutorError("writer or root accounting is unresolved")
            budget.continue_generation(actor=actor, authority_id=authority_id,
                                       predecessor_terminal=True, writers_stopped=True)
            previous = value["revision"]
            value.setdefault("revision_history", []).append({
                "revision": previous, "definition": value["definition"],
                "terminal_state": value["state"], "attempts": value["attempts"],
                "delegation": value.get("delegation"),
                "controller_admission": value.get("controller_admission"),
                "public_assessment": value.get("public_assessment"),
                "routing_decision": value.get("routing_decision"),
                "experimental_policy": value.get("experimental_policy"),
                "terminal_journal_digest": value["journal"][-1]["digest"]})
            definition = dict(value["definition"])
            inputs = definition["input_revision"]["input_paths"]
            definition["input_revision"] = {"git": acceptance.revision(self.project),
                                            "input_paths": inputs,
                                            "content": acceptance.snapshot(self.project, inputs)}
            if acceptance_path is not None:
                frozen = acceptance.load_contract(self.project, acceptance_path)
                definition["acceptance_definition"] = {key: frozen[key] for key in
                                                     ("contract_version", "contract", "contract_digest", "protected_baseline")}
            value["definition"] = definition
            value["definition_digest"] = digest(definition)
            revision = {"revision_number": previous["revision_number"] + 1,
                        "parent_revision_id": previous["revision_id"],
                        "definition_digest": value["definition_digest"],
                        "change_reason": "authorised-continuation", "authority_id": authority_id}
            revision["revision_id"] = digest({**revision, "task_id": value["task_id"]})
            value["revision"] = revision
            value["attempts"] = []
            value.pop("delegation", None)
            value.pop("controller_admission", None)
            value.pop("public_assessment", None)
            value.pop("routing_decision", None)
            policy = value.get("experimental_policy")
            if isinstance(policy, dict) and policy.get("schema_version") == 3:
                baseline = route.plan(*value["axes"])["execution_ladder"]
                pending = {**policy, "policy": PENDING_N3_POLICY,
                           "assessment_digest": None, "selection_digest": None,
                           "selected_cell": None, "ladder": baseline}
                value["experimental_policy"] = pending
                value["ladder"] = baseline
                value["admission"]["policy"] = PENDING_N3_POLICY
                value["admission"]["policy_digest"] = digest(pending)
            value["state"] = "prepared"
            value["block"] = None
            value["owner_generation"] += 1
            _event(value, "revision_started", previous_revision_id=previous["revision_id"],
                   revision_id=revision["revision_id"], actor=actor, reason=reason)
            transition(value, "ready")
            _write(path, value)
        return self.status(root_id)

    def resume(self, root_id: str, *, actor: str, reason: str) -> dict:
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] != "blocked" or not actor.strip() or not reason.strip():
                raise ExecutorError("resume needs a blocked task and operator authority")
            phase = value["block"]["resume_phase"]
            if phase not in {"ready", "verifying", "awaiting_review"}:
                raise ExecutorError("this post-dispatch fault requires closure or validated receipt correction")
            if phase == "ready" and self._budget(root_id).snapshot()["unresolved"]:
                raise ExecutorError("unresolved reservation prevents admission")
            _event(value, "operator_resume", actor=actor, reason=reason)
            transition(value, phase)
            value["block"] = None
            _write(path, value)
        return self.status(root_id)

    def finalise_partial(self, root_id: str, *, actor: str, reason: str) -> dict:
        path = self._path(root_id)
        with route.ledger_lock(path):
            value = _read(path)
            if value["state"] not in {"blocked", "verifying"} or not actor.strip() or not reason.strip():
                raise ExecutorError("partial closure needs blocked/verifying state and operator reason")
            if self._budget(root_id).snapshot()["unresolved"]:
                raise ExecutorError("root accounting unresolved")
            _event(value, "operator_partial", actor=actor, reason=reason)
            transition(value, "partial", reason=reason)
            _write(path, value)
        self._release_claim(root_id)
        return self.status(root_id)


def _overlap(first: list[str], second: list[str]) -> bool:
    return any(a == b or a.startswith(b.rstrip("/") + "/") or b.startswith(a.rstrip("/") + "/")
               for a in first for b in second)


def _read_registry(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        checksum = raw.pop("record_digest")
        if raw.get("schema_version") != 2 or digest(raw) != checksum:
            raise ValueError("registry digest mismatch")
        return raw
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ExecutorError(f"Unreadable project registry {path}: {exc}; preserve it") from exc


def _write_registry(path: Path, value: dict) -> None:
    route._atomic_write_bytes(path, (json.dumps({**value, "record_digest": digest(value)},
                                              indent=2, allow_nan=False) + "\n").encode())


def audit(project: Path) -> dict:
    """Read-only rollback gate; old routing must not redispatch open v2 work."""
    executor = TaskExecutor(project, None)
    roots = []
    if executor.base.exists():
        for path in sorted(executor.base.glob("*/root.json")):
            value = _read(path)
            balance = executor._budget(value["root_id"]).snapshot()
            roots.append({"root_id": value["root_id"], "task_id": value["task_id"],
                          "state": value["state"], "unresolved": balance["unresolved"],
                          "spent_usd": balance["spent_usd"],
                          "reserved_usd": balance["reserved_usd"]})
    unsafe = [row for row in roots if row["state"] not in TERMINAL or row["unresolved"]]
    return {"schema_version": 2, "rollback_safe": not unsafe,
            "roots": roots, "blocking_roots": unsafe}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only worker executor rollback audit")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--audit", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.project)
    except (ExecutorError, dispatch_budget.BudgetError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["rollback_safe"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
