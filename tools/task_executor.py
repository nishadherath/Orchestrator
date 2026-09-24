#!/usr/bin/env python3
"""Durable B0 worker executor for one root task (execution contract v2, N1).

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
import sys
import threading
import re
import secrets
from pathlib import Path

import acceptance
import dispatch_budget
import model_registry
import route
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

    def __init__(self, project: Path, adapter):
        self.project = project.resolve()
        self.adapter = adapter
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

    def override_cell(self, root_id: str, *, cell: str, actor: str, reason: str) -> None:
        """N3 owns selector overrides; N1 cannot silently mutate B0 identity."""
        self.status(root_id)  # Validate the root before reporting an unsupported request.
        raise ExecutorError("cell overrides are unsupported in N1; B0 remains pinned")

    def admit(self, *, goal: str, scope: list[str], permissions: list[str],
              acceptance_path: Path, budget_usd: float, authority_id: str,
              actor: str, root_id: str | None = None, task_id: str | None = None,
              axes: tuple[str, str, str] = ("structured", "medium", "contained"),
              input_paths: list[str] | None = None,
              deadline_at: str | None = None) -> str:
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
        plan = route.plan(*axes)
        if plan["policy"] != "B0" or plan["controller"] is not None or len(plan["execution_ladder"]) != 3:
            raise ExecutorError("qualified B0 policy unavailable")
        ladder = plan["execution_ladder"]
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
                                   "policy": "B0", "policy_digest": digest(ladder),
                                   "deadline_at": deadline_at},
                     "ladder": ladder, "axes": axes, "attempts": [], "journal": [],
                     "owner_generation": 0, "decision_generation": 0,
                     "block": None, "created_at": acceptance.utc_now()}
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

    def run(self, root_id: str) -> dict:
        """Drive B0 until accepted, exhausted, blocked, review or uncertainty.

        A surviving `running` intent is never relaunched. The lock is released
        while a worker or verifier runs; callback generation is checked before
        committing its receipt.
        """
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
                    value["owner_generation"] += 1
                    _event(value, "deadline", deadline_at=deadline_at)
                    transition(value, "cancelled", reason="deadline exceeded")
                    budget.cancel()
                    _write(path, value)
                    return self.status(root_id)
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
                        input_revision = value["definition"]["input_revision"]
                        if acceptance.snapshot(self.project, input_revision["input_paths"])["digest"] != input_revision["content"]["digest"]:
                            raise ExecutorError("frozen task inputs changed before dispatch")
                        capability = self.adapter.capability(self.project)
                        if digest(capability) != value["admission"]["capability_digest"]:
                            raise ExecutorError("host capability changed since admission")
                    except Exception as exc:
                        value["block"] = {"reason": str(exc), "resume_phase": "ready"}
                        transition(value, "blocked", reason=str(exc))
                        _write(path, value)
                        return self.status(root_id)
                    sequence = len(value["attempts"]) + 1
                    cell = value["ladder"][sequence - 1]
                    invocation = secrets.token_hex(16)
                    token = secrets.token_hex(24)
                    decision = {"revision_id": value["revision"]["revision_id"],
                                "sequence": sequence, "policy": "B0", "cell": cell,
                                "cell_resolution": model_registry.resolve_cell(cell),
                                "generation": value["decision_generation"] + 1}
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
                        allowance = budget.reserve(invocation, budget.remaining(), 0.000000001,
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
                    request = WorkerRequest(self.project, value["definition"]["goal"],
                                            tuple(value["definition"]["scope"]), cell,
                                            allowance, "One B0 bounded attempt.",
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
            result = acceptance.verify(self.project, acceptance_state, entry_id)
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
                transition(value, "ready" if len(value["attempts"]) < 3 else "failed")
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
