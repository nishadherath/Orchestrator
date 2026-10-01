#!/usr/bin/env python3
"""Operator CLI for the durable B0 executor; only `run` can call a provider."""
from __future__ import annotations

import argparse
import json
import math
import sys
import threading
from pathlib import Path

import dispatch_budget
import route
import task_executor
import worker_selector
from worker_adapter import CapabilityError, WorkerAdapter


# The interface deliberately excludes campaign dispatch specifications. Those
# require their own frozen evaluation manifest and are not consumer defaults.
FIELDS = {
    "admit": ({"goal", "scope", "acceptance_path", "budget_usd", "authority_id", "actor"},
              {"root_id", "task_id", "axes", "input_paths", "deadline_at"}),
    "cancel": ({"actor", "reason"}, set()),
    "resume": ({"actor", "reason"}, set()),
    "continue": ({"actor", "authority_id", "reason"}, {"acceptance_path"}),
    "review": ({"decision", "reviewer"}, {"notes"}),
    "reconcile": ({"actor", "reason", "cost_usd", "evidence", "writers_stopped"}, set()),
    "partial": ({"actor", "reason"}, set()),
    "shadow": ({"facts"}, {"override"}),
}
ACTIONS = ("audit", "capability", "admit", "status", "run", "cancel", "resume",
           "continue", "review", "reconcile", "partial", "shadow")


def locked_status(executor: task_executor.TaskExecutor, root_id: str) -> dict:
    """Keep Windows readers from holding the root open during atomic replace."""
    with route.ledger_lock(executor._path(root_id)):
        return executor.status(root_id)


def project_status(project: Path) -> dict:
    """Return a locked per-root snapshot; callers still quiesce before rollback."""
    executor = task_executor.TaskExecutor(project, WorkerAdapter())
    roots = []
    for path in sorted(executor.base.glob("*/root.json")):
        value = locked_status(executor, path.parent.name)
        budget = value["budget"]
        roots.append({"root_id": value["root_id"], "task_id": value["task_id"],
                      "state": value["state"], "unresolved": budget["unresolved"],
                      "spent_usd": budget["spent_usd"], "reserved_usd": budget["reserved_usd"]})
    blocking = [row for row in roots if row["state"] not in task_executor.TERMINAL or row["unresolved"]]
    return {"schema_version": 2, "rollback_safe": not blocking,
            "roots": roots, "blocking_roots": blocking}


def request_file(path: Path | None, action: str, project: Path) -> dict:
    """Validate an operation document before any task or budget mutation."""
    if path is None:
        raise task_executor.ExecutorError(f"{action} needs --request <operation.json>")
    if path.stat().st_size > 1_000_000:
        raise task_executor.ExecutorError("operation document exceeds 1 MB")
    value = json.loads(path.read_text(encoding="utf-8"))
    required, optional = FIELDS[action]
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        raise task_executor.ExecutorError(
            f"{action} fields must contain {sorted(required)} and only optional {sorted(optional)}")
    for key in ("goal", "actor", "reason", "authority_id", "reviewer", "decision", "evidence"):
        if key in value and (not isinstance(value[key], str) or not value[key].strip()):
            raise task_executor.ExecutorError(f"{action} {key} must be a non-empty string")
    if "notes" in value and not isinstance(value["notes"], str):
        raise task_executor.ExecutorError(f"{action} notes must be a string")
    if "acceptance_path" in value:
        raw = value["acceptance_path"]
        if not isinstance(raw, str) or not raw or Path(raw).is_absolute():
            raise task_executor.ExecutorError("acceptance_path must be a non-empty project-relative path")
        target = (project / raw).resolve()
        if not target.is_relative_to(project) or target == project:
            raise task_executor.ExecutorError("acceptance_path escapes the consumer project")
        value["acceptance_path"] = target
    if action == "admit":
        for key in ("scope", "input_paths"):
            paths = value.get(key, [])
            if (not isinstance(paths, list) or any(not isinstance(p, str) or not p for p in paths)
                    or (key == "scope" and not paths)):
                raise task_executor.ExecutorError(f"admit {key} must be a list of non-empty paths")
        budget = value["budget_usd"]
        if type(budget) not in (int, float) or not math.isfinite(budget) or budget <= 0:
            raise task_executor.ExecutorError("admit budget_usd must be finite and positive")
        value["permissions"] = ["read", "edit"]
    return value


def run_observed(executor: task_executor.TaskExecutor, root_id: str) -> dict:
    """Own the CLI driver across processes, including receipt reconciliation."""
    lock = executor._path(root_id).with_name("cli-driver")
    with route.ledger_lock(lock, timeout_s=0):
        return _run_observed(executor, root_id)


def _run_observed(executor: task_executor.TaskExecutor, root_id: str) -> dict:
    """Relay durable cancellation to the adapter owned by this run process.

    Another CLI process can mark the root cancelled but cannot address this
    process's subprocess object. The monitor relays that intent. It does not
    infer a stopped writer or zero cost; the normal receipt/recovery path owns
    both. It is not an OS process-tree isolation mechanism.
    """
    results: list[dict] = []
    failures: list[BaseException] = []

    def run() -> None:
        try:
            results.append(executor.run(root_id))
        except BaseException as exc:
            # Exceptions crossing the thread boundary are re-raised below.
            failures.append(exc)

    thread = threading.Thread(target=run, name="worker-execution")
    thread.start()
    signalled: set[str] = set()
    try:
        while thread.is_alive():
            thread.join(0.2)
            if not thread.is_alive():
                break
            value = locked_status(executor, root_id)
            if value["state"] == "cancelled":
                for attempt in value["attempts"]:
                    invocation = attempt["invocation_id"]
                    if attempt["process_state"] == "intent_committed" and invocation not in signalled:
                        cancel = getattr(executor.adapter, "cancel", None)
                        if callable(cancel):
                            cancel(invocation)
                        signalled.add(invocation)
    except KeyboardInterrupt:
        executor.cancel(root_id, actor="operator", reason="CLI interrupted")
    finally:
        thread.join()
    if failures:
        raise failures[0]
    return results[0]


def execute(args: argparse.Namespace, adapter=None) -> dict:
    """Call the existing executor contract without modifying its frozen policy."""
    project = args.project.resolve()
    if not project.is_dir():
        raise task_executor.ExecutorError(f"consumer project does not exist: {project}")
    if args.action == "audit":
        return project_status(project)
    adapter = adapter if adapter is not None else WorkerAdapter(args.mcp_config)
    if args.action == "capability":
        return adapter.capability(project)
    executor = task_executor.TaskExecutor(project, adapter)
    if args.action not in {"admit"} and not args.root:
        raise task_executor.ExecutorError(f"{args.action} needs --root <root-id>")
    if args.action == "status":
        return locked_status(executor, args.root)
    if args.action == "run":
        return run_observed(executor, args.root)
    request = request_file(args.request, args.action, project)
    if args.action == "admit":
        return locked_status(executor, executor.admit(**request))
    if args.action == "shadow":
        return executor.shadow_select(args.root, worker_selector.assess(request["facts"]),
                                      override=request.get("override"))
    method = {"cancel": executor.cancel, "resume": executor.resume,
              "continue": executor.continue_task, "review": executor.review,
              "reconcile": executor.reconcile_uncertain,
              "partial": executor.finalise_partial}[args.action]
    return method(args.root, **request)


def main(argv: list[str], *, adapter=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=ACTIONS)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--root", help="existing durable root id")
    parser.add_argument("--request", type=Path, help="operation JSON; see WORKER-TASKS.md")
    parser.add_argument("--mcp-config", type=Path, help="explicit actor-scoped Graft-only config")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action in {"audit", "capability", "admit"} and args.root is not None:
            raise task_executor.ExecutorError(f"{args.action} does not accept --root")
        if args.action not in FIELDS and args.request is not None:
            raise task_executor.ExecutorError(f"{args.action} does not accept --request")
        result = execute(args, adapter)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        elif "root_id" in result:
            budget = result["budget"]
            print(f"{result['root_id']}: {result['state']} ({result['admission']['policy']})")
            print(f"USD spent={budget['spent_usd']}; held={budget['reserved_usd']}; "
                  f"unresolved={len(budget['unresolved'])}. Use --json for evidence.")
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        if args.action == "audit":
            return 0 if result["rollback_safe"] else 2
        if args.action == "run":
            return 0 if result["state"] == "accepted" else 2
        return 0
    except (OSError, ValueError, TypeError, KeyError, task_executor.ExecutorError,
            CapabilityError, dispatch_budget.BudgetError, route.RoutingError) as exc:
        error = {"result": "BLOCKED", "action": args.action, "error": str(exc)}
        print(json.dumps(error) if args.json else f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
