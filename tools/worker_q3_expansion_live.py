#!/usr/bin/env python3
"""One-shot B0 execution of six calibrated Q3 public families.

The Windows parent writes a durable may-start intent before each WSL child.
An uncertain receipt blocks every later episode and is never replayed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import model_registry
import route
import worker_q3_expansion as plan
from worker_adapter import digest
from worker_q3_public_catalogue import FIXTURES, build, sha

RUN = plan.ROOT / "test/results/2026-09-25-worker-q3-expansion-run"


class LiveExpansionError(RuntimeError):
    """A Q3 public episode or its receipt cannot advance the campaign."""


def save(path: Path, value: dict) -> None:
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    value["state_sha256"] = digest(body)
    route._atomic_write_bytes(path, (json.dumps(value, indent=2, sort_keys=True,
                                               allow_nan=False) + "\n").encode())


def linux_root() -> str:
    process = subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root",
                              "--", "wslpath", "-a", plan.ROOT.as_posix()],
                             capture_output=True, text=True, timeout=30)
    if process.returncode or not process.stdout.strip().startswith("/mnt/"):
        raise LiveExpansionError("repository is unavailable from WSL")
    return process.stdout.strip()


def validate_receipt(row: dict, receipt: dict) -> None:
    attempts = receipt.get("attempts")
    budget = receipt.get("budget") or {}
    hidden = receipt.get("hidden_grade") or {}
    if (receipt.get("task_id") != row["task_id"]
            or receipt.get("root_state") not in {"accepted", "partial", "failed"}
            or budget.get("unresolved") or not isinstance(attempts, list)
            or not 1 <= len(attempts) <= 3
            or type(budget.get("spent_usd")) not in (int, float)
            or not math.isfinite(budget["spent_usd"])
            or budget["spent_usd"] < 0
            or budget["spent_usd"] > row["episode_maximum_usd"]
            or not math.isclose(sum(item.get("cost_usd", float("nan"))
                                    for item in attempts),
                                budget["spent_usd"], abs_tol=1e-8)
            or hidden.get("task_sha256") != row["task_sha256"]
            or hidden.get("task_id") != row["task_id"]
            or hidden.get("root_state") != receipt.get("root_state")
            or hidden.get("oracle_sha256") != row["oracle_sha256"]
            or hidden.get("case_source_sha256") != row["case_source_sha256"]
            or not hidden.get("oracle_read_denied")
            or not hidden.get("source_workspace_unchanged")
            or hidden.get("variant") != "candidate"
            or hidden.get("provider_calls") != 0
            or hidden.get("grade_sha256") != digest({
                key: value for key, value in hidden.items() if key != "grade_sha256"})
            or receipt.get("protected_sha256") != {name: value for name, value in
                row["actor_files"].items() if name not in row["editable_paths"]}):
        raise LiveExpansionError("episode receipt, budget or hidden grade is invalid")
    for index, attempt in enumerate(attempts):
        if (not attempt.get("terminal") or not attempt.get("writer_stopped")
                or not attempt.get("identity_valid")
                or not attempt.get("q1_record_sha256")
                or not attempt.get("q1_spec_sha256")
                or attempt.get("requested_cell") != row["ladder"][index]
                or model_registry.model_class_for_provider_id(
                    attempt.get("actual_model")) != model_registry.resolve_cell(
                        row["ladder"][index])["model"]
                or attempt.get("requested_effort") !=
                    ("high" if index == 2 else "low")
                or type(attempt.get("cost_usd")) not in (int, float)
                or not math.isfinite(attempt["cost_usd"])
                or attempt["cost_usd"] < 0):
            raise LiveExpansionError("attempt identity, effort, isolation or cost is invalid")


def run_campaign() -> dict:
    manifest = json.loads(plan.MANIFEST.read_text(encoding="utf-8"))
    plan.validate(manifest)
    approval = json.loads(plan.APPROVAL.read_text(encoding="utf-8"))
    plan.validate_approval(manifest, approval)
    if RUN.exists():
        raise LiveExpansionError("Q3 expansion run already exists; no automatic replay")
    RUN.mkdir(mode=0o700)
    state = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "status": "running", "created_at_utc":
                 dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "rows": [], "next_sequence": 1, "total_cost_usd": 0.0,
             "total_provider_calls": 0}
    save(RUN / "campaign.json", state)
    linux = linux_root()
    for row in manifest["rows"]:
        plan.validate(manifest)
        plan.validate_approval(manifest, approval)
        if (state["total_cost_usd"] >= manifest["cost"]["combined_allocation_usd"]
                or state["total_provider_calls"] >= manifest["cost"]["maximum_provider_calls"]):
            state["status"] = "blocked"
            state["stop_reason"] = "campaign allocation exhausted"
            save(RUN / "campaign.json", state)
            return state
        item = {"sequence": row["sequence"], "task_id": row["task_id"],
                "state": "provider-call-may-start"}
        state["rows"].append(item)
        save(RUN / "campaign.json", state)
        command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
                   "python3", "-B", f"{linux}/tools/worker_q3_expansion_live.py",
                   "--episode", "--repo", linux, "--task-id", row["task_id"],
                   "--manifest", f"{linux}/{plan.MANIFEST.relative_to(plan.ROOT).as_posix()}",
                   "--approval", f"{linux}/{plan.APPROVAL.relative_to(plan.ROOT).as_posix()}"]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=7200)
            result = json.loads(process.stdout.strip())
            if process.returncode or result.get("result") != "COMPLETE":
                raise LiveExpansionError(result.get("error_type", "episode incomplete"))
            receipt = result["episode"]
            validate_receipt(row, receipt)
        except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired,
                LiveExpansionError) as exc:
            item.update(state="uncertain", failure_type=type(exc).__name__)
            state["status"] = "blocked"
            save(RUN / "campaign.json", state)
            return state
        item.update(state="graded", episode=receipt)
        state["total_cost_usd"] += receipt["budget"]["spent_usd"]
        state["total_provider_calls"] += len(receipt["attempts"])
        state["next_sequence"] = row["sequence"] + 1
        save(RUN / "campaign.json", state)
    state["status"] = "complete"
    save(RUN / "campaign.json", state)
    return state


def run_episode(repo: Path, task_id: str, manifest_path: Path,
                approval_path: Path) -> dict:
    if os.geteuid() != 0 or task_id not in plan.TASKS:
        raise LiveExpansionError("episode requires WSL root and a public task")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    plan.validate_approval(manifest, approval)
    if manifest.get("manifest_sha256") != digest({
            key: value for key, value in manifest.items() if key != "manifest_sha256"}):
        raise LiveExpansionError("Q3 manifest digest is invalid")
    row = next(item for item in manifest["rows"] if item["task_id"] == task_id)
    task = build(task_id)
    frozen = json.loads((FIXTURES / task_id / "task.json").read_text(encoding="utf-8"))
    if (task != frozen or task["task_sha256"] != row["task_sha256"]
            or task["actor_files"] != row["actor_files"]
            or task["editable_paths"] != row["editable_paths"]
            or task["oracle_sha256"] != row["oracle_sha256"]
            or task["case_source_sha256"] != row["case_source_sha256"]
            or row["ladder"] != plan.canary.LADDER
            or row["episode_maximum_usd"] != plan.ALLOCATION
            or manifest["credential_method"] != "claude-code-wsl-subscription"):
        raise LiveExpansionError("Q3 task differs from approved B0 manifest")

    from task_executor import TaskExecutor
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q3_adapter import Q3WslAdapter, isolated_public_runner
    from worker_wsl_q3_public import grade_candidate

    CredentialStore().inspect()
    workspace = SEEDS / f"q3-public-{manifest['manifest_sha256'][:16]}-{task_id.lower()}"
    if workspace.exists() or workspace.is_symlink():
        raise LiveExpansionError("Q3 task workspace already exists; no replay")
    workspace.mkdir(mode=0o700)
    source = repo / "test/fixtures/worker_q3_public" / task_id / "actor"
    for relative, expected in row["actor_files"].items():
        target = workspace / relative
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        data = (source / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise LiveExpansionError("Q3 public source differs from manifest")
        target.write_bytes(data)
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only declared existing source files may change"],
                "required_outputs": row["editable_paths"],
                "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = workspace / ".claude/q3-acceptance.json"
    contract_path.parent.mkdir()
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    executor = TaskExecutor(workspace, Q3WslAdapter(task),
                            command_runner=isolated_public_runner(task))
    root_id = digest({"manifest": manifest["manifest_sha256"],
                      "task_id": task_id})[:24]
    executor.admit(goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
                   scope=row["editable_paths"], permissions=["read", "edit"],
                   acceptance_path=contract_path, budget_usd=plan.ALLOCATION,
                   authority_id=digest({"root": root_id, "authority": "q3"})[:32],
                   actor="q3-b0-public", root_id=root_id, task_id=task_id.lower(),
                   input_paths=protected)
    outcome = executor.run(root_id)
    if outcome["state"] not in {"accepted", "partial", "failed"}:
        raise LiveExpansionError("root outcome needs manual reconciliation")
    hidden = grade_candidate(task_id, workspace, outcome["state"])
    attempts = []
    for attempt in outcome["attempts"]:
        receipt = attempt.get("receipt") or {}
        boundary = receipt.get("command_contract", {}).get("q3_boundary", {})
        attempts.append({"sequence": attempt["sequence"],
                         "requested_cell": attempt["requested_cell"],
                         "requested_effort": receipt.get("requested_effort"),
                         "served_effort": receipt.get("served_effort"),
                         "actual_model": receipt.get("actual_model"),
                         "identity_valid": receipt.get("identity_valid"),
                         "terminal": receipt.get("terminal"),
                         "writer_stopped": receipt.get("writer_stopped"),
                         "cost_usd": receipt.get("cost_usd"),
                         "usage": receipt.get("usage"),
                         "wall_clock_s": receipt.get("wall_clock_s"),
                         "verification": (attempt.get("verification") or {}).get("status"),
                         "q1_record_sha256": boundary.get("q1_record_sha256"),
                         "q1_spec_sha256": boundary.get("q1_spec_sha256"),
                         "changed_paths": boundary.get("changed_paths")})
    return {"task_id": task_id, "root_id": root_id,
            "root_state": outcome["state"], "budget": outcome["budget"],
            "attempts": attempts, "hidden_grade": hidden,
            "workspace": str(workspace),
            "protected_sha256": {name: sha(workspace / name) for name in protected}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--episode", action="store_true")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--task-id")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args()
    try:
        if args.episode:
            if not all((args.repo, args.task_id, args.manifest, args.approval)):
                raise LiveExpansionError("episode arguments are incomplete")
            result = run_episode(args.repo, args.task_id, args.manifest, args.approval)
            print(json.dumps({"result": "COMPLETE", "episode": result}, sort_keys=True))
        elif args.run:
            state = run_campaign()
            print(f"Q3 expansion {state['status']}; {len(state['rows'])} task rows")
            return 0 if state["status"] == "complete" else 2
        else:
            parser.error("choose --run or --episode")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired, StopIteration) as exc:
        if args.episode:
            print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        else:
            print(f"BLOCKED: Q3 expansion: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
