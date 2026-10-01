#!/usr/bin/env python3
"""One-shot Q3 B0 canary driver, requiring an exact approved manifest.

The Windows parent validates the current host before each episode and writes
an intent before starting WSL. An interrupted campaign is never relaunched
automatically. The WSL child runs one durable TaskExecutor root and grades
only after its writer stops.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import route
import worker_q3_canary as plan
from worker_adapter import digest

ROOT = Path(__file__).resolve().parent.parent
APPROVAL = ROOT / "test/results/2026-09-25-worker-q3-canary-approval.json"
RUN = ROOT / "test/results/2026-09-25-worker-q3-canary-run"
NOTICE = ROOT / "docs/stage-results/worker-q3-canary-spend-notice-2026-09-25.md"


class LiveCanaryError(RuntimeError):
    """A Q3 episode cannot advance under the frozen campaign contract."""


def _save(path: Path, value: dict) -> None:
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    value["state_sha256"] = digest(body)
    route._atomic_write_bytes(path, (json.dumps(value, indent=2, sort_keys=True,
                                               allow_nan=False) + "\n").encode())


def validate_approval(manifest: dict, approval: dict) -> None:
    if (not isinstance(approval, dict)
            or set(approval) != {"schema_version", "decision", "manifest_sha256",
                                "maximum_authorised_usd", "maximum_provider_calls",
                                "spend_notice_sha256", "credential_method",
                                "approved_by", "approved_at"}
            or approval["schema_version"] != 1
            or approval["decision"] != "approved"
            or approval["manifest_sha256"] != manifest["manifest_sha256"]
            or approval["maximum_authorised_usd"] != 12.0
            or approval["maximum_provider_calls"] != 6
            or approval["spend_notice_sha256"] != manifest["spend_notice_sha256"]
            or approval["credential_method"] != manifest["credential_method"]
            or not isinstance(approval["approved_by"], str)
            or not approval["approved_by"].strip()
            or not isinstance(approval["approved_at"], str)
            or not approval["approved_at"].strip()):
        raise LiveCanaryError("approval does not match the exact Q3 manifest")


def _linux_root() -> str:
    process = subprocess.run(["wsl.exe", "-u", "root", "--", "wslpath", "-a",
                              ROOT.as_posix()], capture_output=True, text=True, timeout=30)
    if process.returncode or not process.stdout.strip().startswith("/mnt/"):
        raise LiveCanaryError("repository is unavailable from WSL")
    return process.stdout.strip()


def run_campaign() -> dict:
    manifest = json.loads(plan.OUTPUT.read_text(encoding="utf-8"))
    plan.validate(manifest, notice=NOTICE)
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    validate_approval(manifest, approval)
    if RUN.exists():
        raise LiveCanaryError("Q3 run directory already exists; no automatic replay")
    RUN.mkdir(mode=0o700)
    state = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "status": "running", "created_at_utc":
                 dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "rows": [], "next_sequence": 1}
    _save(RUN / "campaign.json", state)
    linux = _linux_root()
    for row in manifest["rows"]:
        # Recheck host, protected task bytes and approval immediately before
        # each independent task. Any drift stops the still-unstarted task.
        plan.validate(manifest, notice=NOTICE)
        validate_approval(manifest, approval)
        item = {"sequence": row["sequence"], "task_id": row["task_id"],
                "state": "provider-call-may-start"}
        state["rows"].append(item)
        _save(RUN / "campaign.json", state)
        command = ["wsl.exe", "-u", "root", "--", "python3", "-B",
                   f"{linux}/tools/worker_q3_live.py", "--episode",
                   "--repo", linux, "--task-id", row["task_id"],
                   "--manifest", f"{linux}/test/results/2026-09-25-worker-q3-canary-manifest.json",
                   "--approval", f"{linux}/test/results/2026-09-25-worker-q3-canary-approval.json"]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=7200)
            result = json.loads(process.stdout.strip())
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            item.update(state="uncertain", failure_type=type(exc).__name__)
            state["status"] = "blocked"
            _save(RUN / "campaign.json", state)
            return state
        if process.returncode or result.get("result") != "COMPLETE":
            item.update(state="uncertain", failure_type=result.get("error_type",
                                                               "episode_incomplete"))
            state["status"] = "blocked"
            _save(RUN / "campaign.json", state)
            return state
        receipt = result["episode"]
        if (receipt["task_id"] != row["task_id"]
                or receipt["root_state"] not in {"accepted", "partial", "failed"}
                or receipt["budget"]["unresolved"]
                or receipt["budget"]["spent_usd"] > row["episode_maximum_usd"]
                or len(receipt["attempts"]) > 3
                or any(type(attempt["cost_usd"]) not in (int, float)
                       for attempt in receipt["attempts"])
                or not math.isclose(
                    sum(attempt["cost_usd"] for attempt in receipt["attempts"]),
                    receipt["budget"]["spent_usd"], abs_tol=1e-8)
                or any(not attempt["terminal"] or not attempt["writer_stopped"]
                       or not attempt["identity_valid"]
                       or not attempt["q1_record_sha256"]
                       or not attempt["q1_spec_sha256"]
                       or attempt["requested_cell"] != row["ladder"][index]
                       or attempt["requested_effort"] !=
                          ("high" if index == 2 else "low")
                       for index, attempt in enumerate(receipt["attempts"]))):
            item.update(state="uncertain", failure_type="unsettled-or-invalid-receipt")
            state["status"] = "blocked"
            _save(RUN / "campaign.json", state)
            return state
        item.update(state="graded", episode=receipt)
        state["next_sequence"] = row["sequence"] + 1
        _save(RUN / "campaign.json", state)
    state["status"] = "complete"
    _save(RUN / "campaign.json", state)
    return state


def run_episode(repo: Path, task_id: str, manifest_path: Path,
                approval_path: Path) -> dict:
    if os.geteuid() != 0 or task_id not in {"P01", "P02"}:
        raise LiveCanaryError("Q3 episode requires WSL root and a public task")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    validate_approval(manifest, approval)
    if manifest.get("manifest_sha256") != digest({
            key: value for key, value in manifest.items() if key != "manifest_sha256"}):
        raise LiveCanaryError("Q3 manifest digest is invalid")
    row = next(item for item in manifest["rows"] if item["task_id"] == task_id)
    if (row["ladder"] != plan.LADDER or row["episode_maximum_usd"] != 6.0
            or manifest["credential_method"] != "claude-code-wsl-subscription"):
        raise LiveCanaryError("Q3 episode differs from approved B0 policy")
    from task_executor import TaskExecutor
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q3_adapter import Q3WslAdapter, isolated_public_runner, sha
    from worker_wsl_q3_grade import grade

    CredentialStore().inspect()
    catalogue = json.loads((repo / "test/fixtures/worker_q2_public/catalogue.json")
                           .read_text(encoding="utf-8"))
    task = next(item for item in catalogue["tasks"] if item["id"] == task_id)
    if (task["actor_files"] != row["actor_files"]
            or task["editable_paths"] != row["editable_paths"]
            or task["oracle_sha256"] != row["oracle_sha256"]):
        raise LiveCanaryError("Q3 catalogue differs from approved task")
    workspace = SEEDS / f"q3-canary-{manifest['manifest_sha256'][:16]}-{task_id.lower()}"
    if workspace.exists() or workspace.is_symlink():
        raise LiveCanaryError("Q3 task workspace already exists; no replay")
    workspace.mkdir(mode=0o700)
    source = repo / "test/fixtures/worker_q2_public" / task_id / "actor"
    for relative, expected in row["actor_files"].items():
        target = workspace / relative
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        data = (source / relative).read_bytes()
        if sha(data) != expected:
            raise LiveCanaryError("Q3 source file differs from approved actor")
        target.write_bytes(data)
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only the two declared source files may change"],
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
                   acceptance_path=contract_path, budget_usd=6.0,
                   authority_id=digest({"root": root_id, "authority": "q3"})[:32],
                   actor="q3-b0-canary", root_id=root_id, task_id=task_id.lower(),
                   input_paths=protected)
    outcome = executor.run(root_id)
    if outcome["state"] not in {"accepted", "partial", "failed"}:
        raise LiveCanaryError("root outcome needs manual reconciliation")
    hidden = grade(repo, workspace, task_id, outcome["state"])
    attempts = []
    for attempt in outcome["attempts"]:
        receipt = attempt.get("receipt") or {}
        boundary = receipt.get("command_contract", {}).get("q3_boundary", {})
        attempts.append({
            "sequence": attempt["sequence"],
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
            "changed_paths": boundary.get("changed_paths"),
        })
    return {"task_id": task_id, "root_id": root_id,
            "root_state": outcome["state"], "budget": outcome["budget"],
            "attempts": attempts, "hidden_grade": hidden,
            "workspace": str(workspace),
            "protected_sha256": {name: sha((workspace / name).read_bytes())
                                 for name in protected}}


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
                raise LiveCanaryError("episode arguments are incomplete")
            result = run_episode(args.repo, args.task_id, args.manifest, args.approval)
            print(json.dumps({"result": "COMPLETE", "episode": result}, sort_keys=True))
        elif args.run:
            state = run_campaign()
            print(f"Q3 campaign {state['status']}; {len(state['rows'])} task rows")
            return 0 if state["status"] == "complete" else 2
        else:
            parser.error("choose --run or --episode")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired, StopIteration) as exc:
        if args.episode:
            print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        else:
            print(f"BLOCKED: Q3 campaign: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
