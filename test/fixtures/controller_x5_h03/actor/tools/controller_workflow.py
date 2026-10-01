"""One-root Controller routing workflow with an explicit operator boundary.

The worker, public assessor and Controller adapters are injected. This module
does not infer operator intent from repository text and does not issue model
calls on import. Root budget and final acceptance remain owned by N1.
"""
from __future__ import annotations

from pathlib import Path

import controller_control
import controller_dispatch
import controller_policy
import controller_profile_policy
import task_executor
import worker_adapter


class WorkflowError(RuntimeError):
    """A routing workflow cannot advance without new evidence or authority."""


def execute(executor: task_executor.TaskExecutor, root_id: str, *,
            issue: str, source_paths: list[str], quote_requests: list[dict],
            interpreter, operational: dict, assessment_allowance_usd: float,
            controller_adapter=None, explicit_mode: str | None = None,
            session_id: str | None = None, controller_profile: str | None = None,
            explicit_experimental_profile: bool = False,
            public_passed: bool = False,
            worker_attempt_limit: int | None = None,
            defer_worker: bool = False) -> dict:
    """Assess once, freeze one decision, then dispatch through the same root.

    A resumed call reuses its persisted assessment and routing decision. New
    controls apply only to a later admission, never to a started invocation.
    An unqualified frontier profile needs an explicitly admitted experimental
    worker root and an explicit profile request; it is never chosen by default.
    """
    if worker_attempt_limit is not None and (
            type(worker_attempt_limit) is not int or worker_attempt_limit < 1):
        raise WorkflowError("worker attempt limit must be a positive integer")
    if type(defer_worker) is not bool:
        raise WorkflowError("defer_worker must be a boolean")
    record = executor.status(root_id)
    if record["state"] in task_executor.TERMINAL | {"blocked", "uncertain", "awaiting_review"}:
        routing = record.get("routing_decision")
        return {"schema_version": 1,
                "decision": routing["decision"] if routing else None,
                "dispatch": None, "task": record}
    if record.get("public_assessment") is None:
        executor.assess_public(
            root_id, issue=issue, source_paths=source_paths,
            quote_requests=quote_requests, interpreter=interpreter,
            operational=operational, maximum_usd=assessment_allowance_usd)
        record = executor.status(root_id)
    elif record["public_assessment"]["status"] != "settled":
        raise WorkflowError("public assessment needs accounting reconciliation")
    if record["admission"]["policy"] == task_executor.PENDING_N3_POLICY:
        record = executor.freeze_public_selection(root_id)

    routing = record.get("routing_decision")
    if routing is None:
        assessment = record["public_assessment"]["result"]["rigour"]
        selection = controller_profile_policy.choose(
            remaining_usd=assessment["authorised_task_budget_usd"],
            experimental_admission=record["admission"]["policy"] ==
            task_executor.EXPERIMENTAL_N3_POLICY,
            requested_profile=controller_profile,
            explicit_experimental=explicit_experimental_profile,
            follow_on_floor_usd=controller_dispatch.FOLLOW_ON_FLOOR_USD)
        control = controller_control.resolve(
            executor.project, explicit_mode=explicit_mode,
            session_id=session_id, task_revision=assessment["task_revision"])
        decision = controller_policy.decide(
            assessment, control, selected_cell=record["ladder"][0],
            controller_profile=selection["profile"],
            public_passed=public_passed)
        record = executor.freeze_routing_decision(
            root_id, decision, session_id=session_id,
            explicit_mode=explicit_mode, profile_selection=selection)
    else:
        decision = routing["decision"]

    action = decision["effective_action"]
    dispatch = None
    if action == "worker":
        task = (executor.status(root_id) if defer_worker else
                executor.run(root_id, stop_after_attempts=worker_attempt_limit))
    elif action in {"blocked", "clarify"}:
        task = executor.block_routing_decision(
            root_id, decision["decision_id"],
            f"routing {action}: {', '.join(decision['reason_codes'])}")
    elif action == "controller":
        admission = record.get("controller_admission") or {}
        if admission.get("status") == "worker-ready":
            executor.accept_controller_handoff(root_id, decision["decision_id"])
            task = (executor.status(root_id) if defer_worker else
                    executor.run(root_id, stop_after_attempts=worker_attempt_limit))
        elif controller_adapter is None:
            task = executor.block_routing_decision(
                root_id, decision["decision_id"],
                "Controller adapter is unavailable")
        else:
            preflight = getattr(controller_adapter, "capability", None)
            if callable(preflight):
                try:
                    preflight(Path(executor.project))
                except worker_adapter.CapabilityError as exc:
                    # This host cannot launch Graft-qualified roles. Keep the
                    # frozen root ready for repair without reserving money.
                    raise WorkflowError(f"Controller host preflight failed: {exc}") from exc
            frozen = record["definition"]
            dispatch = controller_dispatch.TaskDispatcher(
                Path(executor.project), controller_adapter,
                root_task_id=root_id).dispatch(
                    decision, problem_text=frozen["goal"],
                    acceptance_state={key: frozen["acceptance_definition"][key]
                                      for key in ("contract", "contract_digest")},
                    input_revision=frozen["input_revision"])
            if dispatch["stage"] == "worker-ready":
                executor.accept_controller_handoff(root_id, decision["decision_id"])
                task = (executor.status(root_id) if defer_worker else
                        executor.run(root_id, stop_after_attempts=worker_attempt_limit))
            else:
                task = executor.block_routing_decision(
                    root_id, decision["decision_id"],
                    dispatch.get("error") or f"Controller {dispatch['stage']}")
    else:
        raise WorkflowError(f"unsupported routing action: {action}")
    return {"schema_version": 1, "decision": decision,
            "dispatch": dispatch, "task": task}
