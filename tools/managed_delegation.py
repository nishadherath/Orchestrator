#!/usr/bin/env python3
"""Opt-in, durable child DAG for a TaskExecutor root (worker stage N2).

The root executor remains the sole task owner. Every child has one admitted
provider invocation, one root-budget reservation, and independent acceptance.
Parent envelopes are sums of descendant caps, never a second charge. A model's
proposed graph is data: this module validates it before reserving or launching.
"""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import math
import secrets
from pathlib import Path

import acceptance
import dispatch_budget
import model_registry
import route
from task_executor import (ID, TERMINAL, ExecutorError, _event, _overlap, _read,
                           _valid_receipt, _write, transition)
from worker_adapter import WorkerRequest, digest


class DelegationError(ExecutorError):
    """A proposed or active child graph cannot safely advance."""


def _inside(path: str, scopes: list[str]) -> bool:
    return any(path == scope or path.startswith(scope + "/") for scope in scopes)


def _deadline(value: object, root_deadline: str | None) -> str | None:
    if value is None:
        return root_deadline
    if not isinstance(value, str):
        raise DelegationError("child deadline must be a timezone-aware ISO timestamp")
    try:
        when = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        root = (dt.datetime.fromisoformat(root_deadline.replace("Z", "+00:00"))
                if root_deadline else None)
    except ValueError as exc:
        raise DelegationError("invalid child or root deadline") from exc
    if when.tzinfo is None or (root is not None and when > root):
        raise DelegationError("child deadline must be timezone-aware and within root deadline")
    return value


def _validated_plan(executor, root: dict, proposal: dict, capability: dict) -> dict:
    if (not isinstance(proposal, dict) or set(proposal) !=
            {"version", "items", "max_depth", "max_concurrency", "parent_reserve_usd", "parallel_reason"}
            or proposal["version"] != 1):
        raise DelegationError("delegation proposal has unsupported fields or version")
    if (capability.get("managed_delegation_enforced") is not True
            or capability.get("graft_only") is not True
            or capability.get("cancellation_supported") is not True):
        raise DelegationError("host cannot enforce managed children, scoped Graft and cancellation")
    limits = (capability.get("max_child_depth"), capability.get("max_child_concurrency"))
    requested = (proposal["max_depth"], proposal["max_concurrency"])
    if any(type(v) is not int or v < 1 for v in (*limits, *requested)) or any(
            want > host for want, host in zip(requested, limits)):
        raise DelegationError("child depth or concurrency exceeds tested host capability")
    if (not isinstance(proposal["items"], list) or not 1 <= len(proposal["items"]) <= 32):
        raise DelegationError("delegation needs 1-32 bounded child items")
    reason = proposal["parallel_reason"]
    if (not isinstance(reason, str) or len(reason) > 500
            or (requested[1] > 1 and not reason.strip())):
        raise DelegationError("parallel work requires a bounded latency or isolation reason")
    reserve = proposal["parent_reserve_usd"]
    if (type(reserve) not in (int, float) or not math.isfinite(reserve)
            or dispatch_budget.units(reserve) < 1):
        raise DelegationError("a positive root completion allowance is required")
    root_scope = root["definition"]["scope"]
    readable = root_scope + root["definition"]["input_revision"]["input_paths"]
    root_protected = root["definition"]["acceptance_definition"]["contract"]["protected_paths"]
    items: dict[str, dict] = {}
    expected_keys = {"id", "parent_id", "depends_on", "goal", "reads", "writes",
                     "permissions", "acceptance_path", "requested_cell", "allowance_usd", "envelope_usd",
                     "deadline_at", "return_contract"}
    for raw in proposal["items"]:
        if not isinstance(raw, dict) or set(raw) != expected_keys:
            raise DelegationError("child item has missing or unsupported fields")
        child_id = raw["id"]
        if not isinstance(child_id, str) or not ID.fullmatch(child_id) or child_id in items:
            raise DelegationError("child ids must be distinct safe opaque identifiers")
        if (not isinstance(raw["goal"], str) or not raw["goal"].strip()
                or len(raw["goal"]) > 20_000 or raw["permissions"] != ["read", "edit"]
                or raw["return_contract"] != "verified_acceptance"):
            raise DelegationError("child goal, permissions or return contract is invalid")
        if (not isinstance(raw["reads"], list) or not isinstance(raw["writes"], list)
                or not raw["writes"] or not all(isinstance(p, str) for p in raw["reads"] + raw["writes"])):
            raise DelegationError("child read/write paths must be explicit lists")
        reads = [acceptance._relative(executor.project, p)[0] for p in raw["reads"]]
        writes = [acceptance._relative(executor.project, p)[0] for p in raw["writes"]]
        if (any(not _inside(p, readable) for p in reads)
                or any(not _inside(p, root_scope) for p in writes)
                or _overlap(writes, root_protected)
                or any(p == ".claude" or p.startswith(".claude/") for p in writes)):
            raise DelegationError("child paths exceed root authority or touch protected state")
        deps = raw["depends_on"]
        if (not isinstance(deps, list)
                or any(not isinstance(dep, str) or not ID.fullmatch(dep) for dep in deps)
                or len(set(deps)) != len(deps)):
            raise DelegationError("child dependencies must be distinct safe ids")
        parent = raw["parent_id"]
        if parent is not None and (not isinstance(parent, str) or not ID.fullmatch(parent)):
            raise DelegationError("child parent id is invalid")
        cell = model_registry.resolve_cell(raw["requested_cell"])
        if not cell["direct_worker"]:
            raise DelegationError("requested child model/effort is unavailable")
        allowance = raw["allowance_usd"]
        if (type(allowance) not in (int, float) or not math.isfinite(allowance)
                or dispatch_budget.units(allowance) < 1):
            raise DelegationError("child allowance must be finite and positive")
        contract_path = raw["acceptance_path"]
        if not isinstance(contract_path, str):
            raise DelegationError("child acceptance path must be project-relative")
        _, contract_file = acceptance._relative(executor.project, contract_path)
        frozen = acceptance.load_contract(executor.project, contract_file)
        outputs = frozen["contract"]["required_outputs"]
        if (any(not _inside(p, writes) for p in outputs)
                or _overlap(writes, frozen["contract"]["protected_paths"])):
            raise DelegationError("child acceptance outputs or protected paths exceed write authority")
        envelope = raw["envelope_usd"]
        if (type(envelope) not in (int, float) or not math.isfinite(envelope)
                or dispatch_budget.units(envelope) < dispatch_budget.units(allowance)):
            raise DelegationError("child envelope must cover its own call cap")
        items[child_id] = {"id": child_id, "parent_id": parent, "depends_on": deps,
                           "goal": raw["goal"], "reads": reads, "writes": writes,
                           "permissions": ["read", "edit"], "requested_cell": cell["name"],
                           "allowance_usd": allowance, "envelope_usd": envelope,
                           "deadline_at": _deadline(raw["deadline_at"], root["admission"]["deadline_at"]),
                           "return_contract": "verified_acceptance",
                           "acceptance_definition": {key: frozen[key] for key in
                                                     ("contract_version", "contract", "contract_digest",
                                                      "protected_baseline")}}
    for item in items.values():
        if (item["parent_id"] is not None and item["parent_id"] not in items
                or any(dep not in items or dep == item["id"] for dep in item["depends_on"])):
            raise DelegationError("child parent or dependency is missing/self-referential")
        if item["parent_id"] is not None and item["parent_id"] not in item["depends_on"]:
            raise DelegationError("nested child must depend on its executing parent")
    def depth(child_id: str, seen: set[str]) -> int:
        if child_id in seen:
            raise DelegationError("child parent cycle")
        parent = items[child_id]["parent_id"]
        return 1 if parent is None else 1 + depth(parent, seen | {child_id})
    if max(depth(ident, set()) for ident in items) > requested[0]:
        raise DelegationError("child plan exceeds requested depth")
    def subtree_units(child_id: str) -> int:
        return (dispatch_budget.units(items[child_id]["allowance_usd"])
                + sum(subtree_units(ident) for ident, item in items.items()
                      if item["parent_id"] == child_id))
    if any(subtree_units(ident) > dispatch_budget.units(item["envelope_usd"])
           for ident, item in items.items()):
        raise DelegationError("nested child calls exceed parent envelope")
    def ancestors(child_id: str, seen: set[str]) -> set[str]:
        if child_id in seen:
            raise DelegationError("dependency cycle")
        found: set[str] = set()
        for dep in items[child_id]["depends_on"]:
            found.add(dep)
            found.update(ancestors(dep, seen | {child_id}))
        return found
    predecessors = {ident: ancestors(ident, set()) for ident in items}
    for first_id, first in items.items():
        for second_id, second in items.items():
            if first_id >= second_id:
                continue
            conflict = (_overlap(first["writes"], second["writes"] + second["reads"])
                        or _overlap(second["writes"], first["reads"]))
            if conflict and first_id not in predecessors[second_id] and second_id not in predecessors[first_id]:
                raise DelegationError("overlapping child readers/writers need an explicit dependency")
    budget = executor._budget(root["root_id"]).snapshot()
    required_units = sum(dispatch_budget.units(item["envelope_usd"])
                         for item in items.values() if item["parent_id"] is None)
    required_units += dispatch_budget.units(reserve)
    if budget["cancelled"] or budget["breached"] or required_units > dispatch_budget.units(budget["available_usd"]):
        raise DelegationError("child allocations and root completion allowance exceed available budget")
    return {"version": 1, "root_revision_id": root["revision"]["revision_id"],
            "max_depth": requested[0], "max_concurrency": requested[1],
            "parent_reserve_usd": reserve, "parallel_reason": reason,
            "items": items, "capability_digest": digest(capability)}


def cancel_locked(executor, root: dict, budget: dispatch_budget.DispatchBudget,
                  actor: str, reason: str) -> list[str]:
    """Called by TaskExecutor under its root lock; never launches a child."""
    delegation = root["delegation"]
    signals: list[str] = []
    rows = budget.snapshot()["invocations"]
    for child in delegation["children"].values():
        if child["state"] in {"accepted", "failed", "cancelled"}:
            continue
        row = rows.get(child["invocation_id"])
        if row and row["state"] == "reserved":
            budget.settle(child["invocation_id"], 0.0, final=True, telemetry={},
                          evidence="local:root-cancel-before-child-intent")
        elif row and row["state"] != "settled":
            signals.append(child["invocation_id"])
        child["state"] = "cancelled"
    delegation["state"] = "cancelled"
    _event(root, "delegation_cancelled", actor=actor, reason=reason,
           signalled_invocations=signals)
    return signals


class ManagedDelegation:
    """Execute an explicitly admitted static DAG beneath one N1 task root."""

    def __init__(self, executor):
        self.executor = executor

    def admit(self, root_id: str, proposal: dict, *, actor: str, authority_id: str) -> dict:
        if (not isinstance(actor, str) or not actor.strip() or not isinstance(authority_id, str)
                or not ID.fullmatch(authority_id)):
            raise DelegationError("child plan needs operator actor and safe authority id")
        path = self.executor._path(root_id)
        with route.ledger_lock(path):
            root = _read(path)
            if root["state"] != "ready" or root["attempts"] or root.get("delegation"):
                raise DelegationError("child plan needs an unused ready root and one authority")
            capability = self.executor.adapter.capability(self.executor.project)
            try:
                plan = _validated_plan(self.executor, root, proposal, capability)
            except (acceptance.AcceptanceError, model_registry.RegistryError,
                    dispatch_budget.BudgetError) as exc:
                raise DelegationError(f"invalid child proposal: {exc}") from exc
            plan_digest = digest(plan)
            children = {}
            for ident, item in plan["items"].items():
                children[ident] = {"state": "pending", "invocation_id": "child-" +
                                   digest({"root": root_id, "revision": plan["root_revision_id"],
                                           "child": ident})[:32],
                                   "admission_token": None, "revision_id": digest(
                                       {"root_revision": plan["root_revision_id"],
                                        "child": ident, "plan": plan_digest}),
                                   "decision_digest": None, "intent_digest": None,
                                   "generation": 0, "receipt": None, "receipt_digest": None,
                                   "verification": None, "artefact_snapshot": None,
                                   "late_receipts": []}
            root["delegation"] = {"version": 1, "state": "reserving", "plan": plan,
                                  "plan_digest": plan_digest, "authority_id": authority_id,
                                  "actor": actor, "children": children}
            _event(root, "delegation_admitted", authority_id=authority_id,
                   plan_digest=plan_digest, child_ids=sorted(children))
            _write(path, root)
            self._ensure_reservations(root)
            return self.executor.status(root_id)

    def _ensure_reservations(self, root: dict) -> None:
        delegation = root["delegation"]
        budget = self.executor._budget(root["root_id"])
        rows = budget.snapshot()["invocations"]
        for ident, child in delegation["children"].items():
            item = delegation["plan"]["items"][ident]
            invocation = child["invocation_id"]
            metadata = {"root_id": root["root_id"], "child_id": ident,
                        "plan_digest": delegation["plan_digest"]}
            if invocation not in rows:
                allowance = budget.reserve(invocation, item["allowance_usd"],
                                           item["allowance_usd"], metadata)
                if dispatch_budget.units(allowance) != dispatch_budget.units(item["allowance_usd"]):
                    raise DelegationError("child reservation was truncated")
            elif (rows[invocation]["metadata"] != metadata
                  or rows[invocation]["allowance_units"] != dispatch_budget.units(item["allowance_usd"])):
                raise DelegationError("child reservation conflicts with frozen plan")
        if delegation["state"] == "reserving":
            delegation["state"] = "active"
            _event(root, "delegation_reserved", child_ids=sorted(delegation["children"]))
            _write(self.executor._path(root["root_id"]), root)

    def _prepare(self, root_id: str, child_id: str) -> WorkerRequest:
        path = self.executor._path(root_id)
        with route.ledger_lock(path):
            root = _read(path)
            delegation = root["delegation"]
            child = delegation["children"][child_id]
            item = delegation["plan"]["items"][child_id]
            if (root["state"] != "ready" or delegation["state"] != "active"
                    or child["state"] != "pending"
                    or any(delegation["children"][dep]["state"] != "accepted"
                           for dep in item["depends_on"])):
                raise DelegationError("child is not ready for admission")
            when = item["deadline_at"]
            if when and dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(when.replace("Z", "+00:00")):
                child["state"] = "failed"
                _event(root, "child_deadline_before_dispatch", child_id=child_id)
                self._block_root(root, "required child deadline expired")
                _write(path, root)
                raise DelegationError("child deadline expired before dispatch")
            try:
                capability = self.executor.adapter.capability(self.executor.project)
            except Exception as exc:
                self._block_root(root, f"managed child host capability unavailable: {exc}")
                _write(path, root)
                raise DelegationError("managed child host capability unavailable") from exc
            if digest(capability) != delegation["plan"]["capability_digest"]:
                self._block_root(root, "managed child host capability changed")
                _write(path, root)
                raise DelegationError("managed child host capability changed")
            budget = self.executor._budget(root_id)
            row = budget.snapshot()["invocations"][child["invocation_id"]]
            if row["state"] != "reserved":
                self._block_root(root, "child reservation is not unused")
                _write(path, root)
                raise DelegationError("child reservation is not unused")
            child["admission_token"] = secrets.token_hex(24)
            child["decision_digest"] = digest({"revision_id": child["revision_id"],
                                               "cell": item["requested_cell"],
                                               "plan_digest": delegation["plan_digest"]})
            child["state"] = "admitted"
            _event(root, "child_admitted", child_id=child_id,
                   invocation_id=child["invocation_id"],
                   decision_digest=child["decision_digest"])
            _write(path, root)
            budget.start(child["invocation_id"])
            root["owner_generation"] += 1
            child["generation"] = root["owner_generation"]
            intent = {"invocation_id": child["invocation_id"],
                      "revision_id": child["revision_id"],
                      "decision_digest": child["decision_digest"],
                      "admission_token": child["admission_token"],
                      "generation": child["generation"]}
            child["intent_digest"] = digest(intent)
            child["state"] = "running"
            _event(root, "child_host_intent", child_id=child_id, intent=intent)
            _write(path, root)
            remaining = (dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
                         - dt.datetime.now(dt.timezone.utc)).total_seconds() if when else 900.0
            return WorkerRequest(self.executor.project, item["goal"], tuple(item["writes"]),
                                 item["requested_cell"], item["allowance_usd"],
                                 "One admitted child action; return evidence for independent verification.",
                                 timeout_s=max(0.001, min(900.0, remaining)),
                                 admission_token=child["admission_token"],
                                 invocation_id=child["invocation_id"],
                                 revision_id=child["revision_id"],
                                 decision_digest=child["decision_digest"],
                                 intent_digest=child["intent_digest"])

    def _block_root(self, root: dict, reason: str) -> None:
        """Stop admission and release only children proven never dispatched."""
        budget = self.executor._budget(root["root_id"])
        rows = budget.snapshot()["invocations"]
        for ident, child in root["delegation"]["children"].items():
            if child["state"] not in {"pending", "admitted"}:
                continue
            row = rows.get(child["invocation_id"])
            if row and row["state"] == "reserved":
                budget.settle(child["invocation_id"], 0.0, final=True,
                              telemetry={}, evidence="local:delegation-block-before-intent")
                child["state"] = "dependency_blocked"
                child["block_reason"] = reason
                _event(root, "child_not_dispatched", child_id=ident, reason=reason)
            elif row and row["state"] != "settled":
                child["state"] = "uncertain"
        if root["state"] == "ready":
            root["block"] = {"reason": reason, "resume_phase": None}
            transition(root, "blocked", reason=reason)
        root["delegation"]["state"] = "blocked"

    def _record_receipt(self, root_id: str, child_id: str, receipt: dict, generation: int) -> bool:
        path = self.executor._path(root_id)
        with route.ledger_lock(path):
            root = _read(path)
            child = root["delegation"]["children"][child_id]
            item = root["delegation"]["plan"]["items"][child_id]
            receipt_digest = digest(receipt)
            if child["receipt_digest"]:
                if child["receipt_digest"] == receipt_digest:
                    return child["state"] == "verifying"
                child.setdefault("conflicting_receipts", []).append(receipt)
                _event(root, "conflicting_child_receipt", child_id=child_id,
                       receipt_digest=receipt_digest)
                _write(path, root)
                raise DelegationError("conflicting child receipt retained")
            identity = {"admission_token": child["admission_token"],
                        "invocation_id": child["invocation_id"],
                        "revision_id": child["revision_id"],
                        "decision_digest": child["decision_digest"],
                        "intent_digest": child["intent_digest"],
                        "requested_cell": item["requested_cell"]}
            if any(receipt.get(key) != expected for key, expected in identity.items()):
                child.setdefault("conflicting_receipts", []).append(receipt)
                _event(root, "unmatched_child_receipt", child_id=child_id,
                       receipt_digest=receipt_digest)
                if child["state"] == "running":
                    child["state"] = "uncertain"
                    self._block_root(root, "child receipt identity mismatch")
                _write(path, root)
                raise DelegationError("child receipt does not match admission")
            late = child["state"] != "running" or child["generation"] != generation
            if late and any(row["digest"] == receipt_digest for row in child["late_receipts"]):
                return False
            if late:
                child["late_receipts"].append({"digest": receipt_digest, "receipt": receipt})
            else:
                child["receipt"] = receipt
                child["receipt_digest"] = receipt_digest
            _event(root, "late_child_receipt" if late else "child_receipt",
                   child_id=child_id, receipt_digest=receipt_digest)
            _write(path, root)  # Raw receipt precedes cross-file settlement.
            if receipt.get("terminal") and receipt.get("writer_stopped") and receipt.get("cost_usd") is not None:
                budget = self.executor._budget(root_id)
                row = budget.snapshot()["invocations"][child["invocation_id"]]
                if row["state"] != "settled":
                    budget.settle(child["invocation_id"], receipt["cost_usd"], final=True,
                                  telemetry=receipt.get("usage") or {},
                                  evidence=f"child-receipt:{receipt_digest}")
            elif not late:
                child["state"] = "uncertain"
                self._block_root(root, "child cost or writer termination uncertain")
            if not late:
                if child["state"] == "running":
                    if _valid_receipt({"requested_cell": item["requested_cell"]}, receipt):
                        child["state"] = "verifying"
                    else:
                        child["state"] = "blocked"
                        self._block_root(root, "child model, effort or process mismatch")
                _event(root, "child_receipt_reconciled", child_id=child_id,
                       child_state=child["state"])
            _write(path, root)
            return child["state"] == "verifying" and not late

    def _verify(self, root_id: str, child_id: str, generation: int) -> None:
        path = self.executor._path(root_id)
        with route.ledger_lock(path):
            root = _read(path)
            child = root["delegation"]["children"][child_id]
            if child["state"] != "verifying" or child["generation"] != generation:
                return
            frozen = root["delegation"]["plan"]["items"][child_id]["acceptance_definition"]
            entry_id = f"{root_id}-child-{child_id}-{root['revision']['revision_number']}"
        state = {**frozen, "status": "pending", "evidence": None, "review": None}
        try:
            result = acceptance.verify(self.executor.project, state, entry_id)
            snapshot = self.executor._snapshot_artefacts(root_id, entry_id, result)
            root_frozen = root["definition"]["acceptance_definition"]
            protected = acceptance.snapshot(self.executor.project,
                                            root_frozen["contract"]["protected_paths"])
            root_protected_ok = protected["digest"] == root_frozen["protected_baseline"]["digest"]
        except Exception as exc:
            self._fault(root_id, child_id, generation, f"child verifier error: {exc}")
            return
        with route.ledger_lock(path):
            root = _read(path)
            child = root["delegation"]["children"][child_id]
            if child["state"] != "verifying" or child["generation"] != generation:
                _event(root, "late_child_verification", child_id=child_id,
                       result_digest=digest(result))
                _write(path, root)
                return
            child["verification"] = result
            child["artefact_snapshot"] = snapshot
            if not root_protected_ok or not result["evidence"]["protected_unchanged"]:
                child["state"] = "blocked"
                self._block_root(root, "protected path changed during child work")
            elif result["status"] == "pass" and acceptance.qualified(result):
                child["state"] = "accepted"
            elif result["status"] == "review_required":
                child["state"] = "awaiting_review"
            elif result["status"] == "fail" and acceptance.qualified(result):
                child["state"] = "failed"
                self._block_root(root, "required child failed independent acceptance")
            else:
                child["state"] = "blocked"
                self._block_root(root, "child verification blocked or unqualified")
            _event(root, "child_verified", child_id=child_id, state=child["state"])
            _write(path, root)

    def _fault(self, root_id: str, child_id: str, generation: int, reason: str) -> None:
        path = self.executor._path(root_id)
        with route.ledger_lock(path):
            root = _read(path)
            child = root["delegation"]["children"][child_id]
            if child["generation"] != generation or child["state"] not in {"running", "verifying"}:
                return
            child["state"] = "uncertain" if child["state"] == "running" else "blocked"
            self._block_root(root, reason)
            _event(root, "child_fault", child_id=child_id, reason=reason,
                   state=child["state"])
            _write(path, root)

    def _invoke(self, root_id: str, child_id: str, request: WorkerRequest, generation: int) -> None:
        timer = self.executor._deadline_timer(root_id,
            self.executor.status(root_id)["delegation"]["plan"]["items"][child_id]["deadline_at"])
        try:
            receipt = self.executor.adapter.run(request)
            if self._record_receipt(root_id, child_id, receipt, generation):
                self._verify(root_id, child_id, generation)
        except Exception as exc:
            self._fault(root_id, child_id, generation, f"child adapter or receipt error: {exc}")
        finally:
            if timer is not None:
                timer.cancel()

    def run(self, root_id: str) -> dict:
        """Own one runner across processes while permitting concurrent cancellation."""
        self.executor._path(root_id)
        with route.ledger_lock(self.executor.base / root_id / "delegation-run", timeout_s=0):
            return self._run_owned(root_id)

    def _run_owned(self, root_id: str) -> dict:
        """Run ready waves; recover receipts, never replay ambiguous intents."""
        path = self.executor._path(root_id)
        while True:
            snapshot = self.executor.status(root_id)
            delegation = snapshot.get("delegation")
            if delegation and snapshot["state"] not in TERMINAL and delegation["state"] == "active":
                now = dt.datetime.now(dt.timezone.utc)
                for ident, item in delegation["plan"]["items"].items():
                    due = item["deadline_at"]
                    if (due and delegation["children"][ident]["state"] not in
                            {"accepted", "failed", "cancelled", "dependency_blocked"}
                            and now >= dt.datetime.fromisoformat(due.replace("Z", "+00:00"))):
                        return self.executor.cancel(root_id, actor="deadline",
                                                    reason=f"required child {ident} deadline exceeded")
            recover_verification: list[tuple[str, int]] = []
            with route.ledger_lock(path):
                root = _read(path)
                delegation = root.get("delegation")
                if delegation is None:
                    raise DelegationError("no managed child plan admitted")
                if root["state"] in TERMINAL or delegation["state"] in {"complete", "blocked", "cancelled"}:
                    return self.executor.status(root_id)
                self._ensure_reservations(root)
                rows = self.executor._budget(root_id).snapshot()["invocations"]
                for child_id, child in delegation["children"].items():
                    row = rows[child["invocation_id"]]
                    if child["state"] == "pending" and row["state"] != "reserved":
                        child["state"] = "uncertain"
                        self._block_root(root, "pending child has a non-reserved allocation")
                        _event(root, "child_allocation_conflict", child_id=child_id)
                    if child["state"] == "admitted" and row["state"] == "reserved":
                        self.executor._budget(root_id).settle(child["invocation_id"], 0.0,
                            final=True, telemetry={}, evidence="local:child-pre-start-recovery")
                        child["state"] = "pending"
                        child["admission_token"] = None
                        child["decision_digest"] = None
                        child["intent_digest"] = None
                        _event(root, "child_pre_start_recovered", child_id=child_id)
                        # A fresh invocation is required: settled ids never authorise replay.
                        child["invocation_id"] = "child-" + digest(
                            {"root": root_id, "child": child_id, "recovery": len(root["journal"])})[:32]
                    elif child["state"] == "running" and child["receipt"] is not None:
                        receipt = child["receipt"]
                        valid = (receipt.get("terminal") and receipt.get("writer_stopped")
                                 and receipt.get("cost_usd") is not None)
                        if valid:
                            if row["state"] != "settled":
                                self.executor._budget(root_id).settle(child["invocation_id"],
                                    receipt["cost_usd"], final=True,
                                    telemetry=receipt.get("usage") or {},
                                    evidence=f"child-receipt:{child['receipt_digest']}")
                            requested = delegation["plan"]["items"][child_id]["requested_cell"]
                            if _valid_receipt({"requested_cell": requested}, receipt):
                                child["state"] = "verifying"
                                recover_verification.append((child_id, child["generation"]))
                            else:
                                child["state"] = "blocked"
                                self._block_root(root, "recovered child identity fault")
                        else:
                            child["state"] = "uncertain"
                            self._block_root(root, "incomplete persisted child receipt")
                        _event(root, "child_receipt_recovered", child_id=child_id,
                               state=child["state"])
                    elif child["state"] == "verifying":
                        recover_verification.append((child_id, child["generation"]))
                    elif child["state"] in {"admitted", "running"}:
                        child["state"] = "uncertain"
                        self._block_root(root, "child dispatch intent survived without terminal receipt")
                        _event(root, "child_recovery_uncertain", child_id=child_id)
                if delegation["state"] != "blocked":
                    self._ensure_reservations(root)
                _write(path, root)
                if delegation["state"] == "blocked":
                    return self.executor.status(root_id)
                if recover_verification:
                    ready = []
                elif all(child["state"] == "accepted" for child in delegation["children"].values()):
                    delegation["state"] = "complete"
                    _event(root, "delegation_complete", child_ids=sorted(delegation["children"]))
                    _write(path, root)
                    return self.executor.status(root_id)
                else:
                    ready = sorted(ident for ident, item in delegation["plan"]["items"].items()
                                   if delegation["children"][ident]["state"] == "pending"
                                   and all(delegation["children"][dep]["state"] == "accepted"
                                           for dep in item["depends_on"]))
                    ready = ready[:delegation["plan"]["max_concurrency"]]
                    if not ready:
                        return self.executor.status(root_id)
            if recover_verification:
                for ident, generation in recover_verification:
                    self._verify(root_id, ident, generation)
                continue
            requests = []
            for ident in ready:
                try:
                    request = self._prepare(root_id, ident)
                except DelegationError:
                    return self.executor.status(root_id)
                requests.append((ident, request))
            if len(requests) == 1:
                ident, request = requests[0]
                self._invoke(root_id, ident, request,
                             self.executor.status(root_id)["delegation"]["children"][ident]["generation"])
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(requests)) as pool:
                    futures = [pool.submit(self._invoke, root_id, ident, request,
                              self.executor.status(root_id)["delegation"]["children"][ident]["generation"])
                               for ident, request in requests]
                    for future in futures:
                        future.result()

    def review_child(self, root_id: str, child_id: str, *, decision: str,
                     reviewer: str, notes: str = "") -> dict:
        path = self.executor._path(root_id)
        with route.ledger_lock(path):
            root = _read(path)
            child = root["delegation"]["children"][child_id]
            if child["state"] != "awaiting_review" or root["state"] != "ready":
                raise DelegationError("child is not awaiting review")
            entry_id = f"{root_id}-child-{child_id}-{root['revision']['revision_number']}"
            result = acceptance.review(self.executor.project, child["verification"], entry_id,
                                       decision, reviewer, notes)
            child["verification"] = result
            child["state"] = "accepted" if result["status"] == "pass" and acceptance.qualified(result) else "failed"
            if child["state"] == "failed":
                self._block_root(root, "required child failed review")
            _event(root, "child_reviewed", child_id=child_id, state=child["state"], reviewer=reviewer)
            _write(path, root)
        return self.executor.status(root_id)

    def reconcile_child(self, root_id: str, child_id: str, *, actor: str,
                        evidence: str, cost_usd: float, writers_stopped: bool) -> dict:
        if not actor.strip() or not evidence.strip() or writers_stopped is not True:
            raise DelegationError("child reconciliation needs actor, evidence and stopped-writer proof")
        path = self.executor._path(root_id)
        with route.ledger_lock(path):
            root = _read(path)
            child = root["delegation"]["children"][child_id]
            if child["state"] not in {"uncertain", "cancelled"}:
                raise DelegationError("child is not uncertain or cancelled")
            budget = self.executor._budget(root_id)
            row = budget.snapshot()["invocations"][child["invocation_id"]]
            if row["state"] == "settled":
                if dispatch_budget.units(cost_usd, ceiling=True) != row["charged_units"]:
                    raise DelegationError("reconciliation conflicts with settled child charge")
            else:
                budget.settle(child["invocation_id"], cost_usd, final=True,
                              telemetry={"reconciled_by": actor}, evidence=evidence)
            child.setdefault("reconciliations", []).append(
                {"actor": actor, "evidence": evidence, "cost_usd": cost_usd})
            if root["state"] != "cancelled":
                child["state"] = "failed"  # No automatic replay or quality retry.
                self._block_root(root, "uncertain child reconciled without accepted work")
            _event(root, "child_reconciled", child_id=child_id, actor=actor,
                   evidence=evidence, cost_usd=cost_usd)
            _write(path, root)
        return self.executor.status(root_id)
