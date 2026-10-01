#!/usr/bin/env python3
"""Continue Q4 M3 at sequence 4 while preserving a settled terminal failure."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import model_registry
import route
import worker_q4_screen as original
import worker_q4_screen_live as live
from worker_adapter import digest
from worker_q3_public_catalogue import build, sha

ROOT = original.ROOT
NOTICE = ROOT / "docs/stage-results/worker-q4-m3-continuation-spend-notice-2026-09-26.md"
MANIFEST = ROOT / "test/results/2026-09-26-worker-q4-m3-continuation-manifest.json"
APPROVAL = ROOT / "test/results/2026-09-26-worker-q4-m3-continuation-approval.json"
RECONCILIATION = ROOT / "test/results/2026-09-26-worker-q4-m3-reconciliation.json"
RUN = ROOT / "test/results/2026-09-26-worker-q4-m3-continuation-run"
FIRST_SEQUENCE = 4
NEW_MAXIMUM_USD = 78.0
NEW_MAXIMUM_CALLS = 39
SOURCES = (
    "tools/worker_q4_screen.py", "tools/worker_q4_screen_live.py",
    "tools/worker_q4_reconcile.py", "tools/worker_q4_screen_continue.py",
    "tools/worker_wsl_q4_adapter.py", "tools/worker_quality_v2.py",
    "tools/task_executor.py", "tools/worker_adapter.py",
)


class ContinuationError(RuntimeError):
    """The no-replay M3 continuation cannot safely advance."""


def _sealed(path: Path, field: str) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get(field) != digest({key: item for key, item in value.items()
                                   if key != field}):
        raise ContinuationError(f"sealed evidence is invalid: {path.name}")
    return value


def predecessor() -> tuple[dict, dict, dict, list[dict]]:
    manifest = json.loads(original.MANIFEST.read_text(encoding="utf-8"))
    original.validate(manifest, check_host=True)
    approval = json.loads(original.APPROVAL.read_text(encoding="utf-8"))
    original.validate_approval(manifest, approval)
    campaign = _sealed(live.RUN / "campaign.json", "state_sha256")
    reconciliation = _sealed(RECONCILIATION, "evidence_sha256")
    if (campaign.get("status") != "blocked" or len(campaign.get("rows", [])) != 3
            or [row.get("state") for row in campaign["rows"]]
                != ["graded", "graded", "uncertain"]
            or reconciliation.get("manifest_sha256") != manifest["manifest_sha256"]
            or reconciliation.get("campaign_state_sha256") != campaign["state_sha256"]
            or reconciliation.get("campaign_file_sha256") != sha(live.RUN / "campaign.json")
            or reconciliation.get("reconciliation_provider_calls") != 0
            or reconciliation.get("reconciliation_provider_cost_usd") != 0
            or reconciliation.get("episode", {}).get("terminal_failure") is not True
            or reconciliation["episode"].get("episode_label") != "sonnet-xhigh"):
        raise ContinuationError("predecessor or no-replay reconciliation changed")
    inherited = [campaign["rows"][0]["episode"],
                 campaign["rows"][1]["episode"], reconciliation["episode"]]
    return manifest, campaign, reconciliation, inherited


def build_manifest(date_utc: str, notice_sha256: str) -> dict:
    if dt.date.fromisoformat(date_utc) != dt.datetime.now(dt.timezone.utc).date():
        raise ContinuationError("continuation must be frozen on today's UTC date")
    prior, campaign, reconciliation, inherited = predecessor()
    remaining = [row for row in prior["rows"] if row["sequence"] >= FIRST_SEQUENCE]
    spent = campaign["total_cost_usd"] + reconciliation["inherited_provider_cost_usd"]
    calls = campaign["total_provider_calls"] + reconciliation["inherited_provider_calls"]
    value = {"schema_version": 1,
             "profile": "worker-q4-m3-no-replay-continuation",
             "date_utc": date_utc,
             "credential_method": "claude-code-wsl-subscription",
             "spend_notice_sha256": notice_sha256,
             "predecessor_manifest_sha256": prior["manifest_sha256"],
             "predecessor_campaign_sha256": sha(live.RUN / "campaign.json"),
             "predecessor_state_sha256": campaign["state_sha256"],
             "reconciliation_sha256": sha(RECONCILIATION),
             "reconciliation_evidence_sha256": reconciliation["evidence_sha256"],
             "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
             "host_evidence_sha256": prior["host_evidence_sha256"],
             "calibration_evidence_sha256": prior["calibration_evidence_sha256"],
             "inherited_sequences": [1, 2, 3],
             "remaining_sequences": list(range(FIRST_SEQUENCE, 17)),
             "rows": remaining,
             "cost": {"currency": "USD", "prior_spent_usd": spent,
                      "prior_provider_calls": calls,
                      "new_maximum_usd": NEW_MAXIMUM_USD,
                      "new_maximum_provider_calls": NEW_MAXIMUM_CALLS,
                      "combined_maximum_usd": spent + NEW_MAXIMUM_USD,
                      "combined_maximum_provider_calls": calls + NEW_MAXIMUM_CALLS,
                      "api_equivalent_projection_usd": [3.0, 50.0]},
             "selection_rules": prior["selection_rules"],
             "reserved_repetition_rule": prior["reserved_repetition_rule"],
             "stop_rules": ["No replay of inherited or started sequences",
                            "Record settled terminal provider failures as outcomes",
                            "Stop on nonterminal, uncertain-cost or identity-ambiguous receipt",
                            "Stop on stale host, calibration, source or predecessor evidence"],
             "reserved_tasks_allowed": False, "controller_allowed": False,
             "authorisation": "operator-standing-through-Q4-2026-09-25"}
    if (len(inherited) != 3 or len(remaining) != 13
            or [row["sequence"] for row in remaining] != list(range(4, 17))
            or spent + NEW_MAXIMUM_USD > 99
            or calls + NEW_MAXIMUM_CALLS > 51):
        raise ContinuationError("continuation exceeds the predecessor envelope")
    return {**value, "manifest_sha256": digest(value)}


def validate(manifest: dict) -> None:
    if NOTICE.is_symlink() or sha(NOTICE) != manifest.get("spend_notice_sha256"):
        raise ContinuationError("continuation notice differs")
    if manifest != build_manifest(manifest["date_utc"], sha(NOTICE)):
        raise ContinuationError("continuation manifest differs from current evidence")


def validate_approval(manifest: dict, approval: dict) -> None:
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_new_usd": NEW_MAXIMUM_USD,
                "maximum_new_provider_calls": NEW_MAXIMUM_CALLS,
                "spend_notice_sha256": manifest["spend_notice_sha256"],
                "credential_method": manifest["credential_method"],
                "approved_by": "operator-standing-through-Q4-2026-09-25"}
    if (not isinstance(approval, dict)
            or {key: approval.get(key) for key in expected} != expected
            or set(approval) != set(expected) | {"approved_at"}
            or not isinstance(approval.get("approved_at"), str)):
        raise ContinuationError("approval is not bound to this continuation")


def save(path: Path, value: dict) -> None:
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    value["state_sha256"] = digest(body)
    route._atomic_write_bytes(path, (json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def preserve(row: dict, workspace: Path) -> dict:
    target = RUN / "patches" / f"{row['sequence']:02d}-{row['task_id'].lower()}-{row['episode_label']}"
    if target.exists():
        raise ContinuationError("candidate snapshot already exists")
    files = {}
    for relative in row["editable_paths"]:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(workspace / relative, destination)
        files[relative] = sha(destination)
    value = {"schema_version": 1, "sequence": row["sequence"],
             "task_id": row["task_id"], "episode_label": row["episode_label"],
             "files": files}
    value["snapshot_sha256"] = digest(value)
    (target / "snapshot.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def project_attempt(attempt: dict, row: dict, *, allow_failure: bool) -> dict:
    receipt = attempt.get("receipt") or {}
    boundary = receipt.get("command_contract", {}).get("q4_boundary", {})
    expected = model_registry.resolve_cell(attempt["requested_cell"])["cli_model"]
    real_roots = sorted(model for model in receipt.get("root_models", [])
                        if model != "<synthetic>")
    reconciled = bool(allow_failure and receipt.get("status") == "failed"
                      and real_roots == [expected])
    report = receipt.get("evaluation_report") or {}
    return {"sequence": attempt["sequence"],
            "requested_cell": attempt["requested_cell"],
            "requested_effort": receipt.get("requested_effort"),
            "served_effort": receipt.get("served_effort"),
            "actual_model": receipt.get("actual_model") or (
                expected if reconciled else None),
            "identity_valid": bool(receipt.get("identity_valid") or reconciled),
            "receipt_identity_valid": receipt.get("identity_valid"),
            "identity_reconciled": reconciled,
            "terminal": receipt.get("terminal"),
            "writer_stopped": receipt.get("writer_stopped"),
            "status": receipt.get("status"), "returncode": receipt.get("returncode"),
            "cost_usd": receipt.get("cost_usd"), "usage": receipt.get("usage"),
            "wall_clock_s": receipt.get("wall_clock_s"),
            "verification": (attempt.get("verification") or {}).get("status"),
            "q1_record_sha256": boundary.get("q1_record_sha256"),
            "q1_spec_sha256": boundary.get("q1_spec_sha256"),
            "changed_paths": boundary.get("changed_paths"),
            "evaluation_report": report,
            "evaluation_report_digest": receipt.get("evaluation_report_digest"),
            "original_receipt_digest": attempt.get("receipt_digest")}


def episode(repo: Path, row: dict, manifest: dict) -> dict:
    from task_executor import TaskExecutor
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q3_adapter import isolated_public_runner
    from worker_wsl_q4_adapter import Q4WslAdapter

    task = build(row["task_id"])
    _, rubric = original.live_rubric(row["task_id"])
    CredentialStore().inspect()
    name = f"q4-m3c-{manifest['manifest_sha256'][:12]}-{row['sequence']:02d}"
    workspace = SEEDS / name
    if workspace.exists() or workspace.is_symlink():
        raise ContinuationError("continuation workspace already exists; no replay")
    workspace.mkdir(mode=0o700)
    source = repo / "test/fixtures/worker_q3_public" / row["task_id"] / "actor"
    for relative, expected in row["actor_files"].items():
        target = workspace / relative
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        data = (source / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ContinuationError("public source differs")
        target.write_bytes(data)
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only declared existing source files may change"],
                "required_outputs": row["editable_paths"],
                "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = workspace / ".claude/q4-acceptance.json"
    contract_path.parent.mkdir()
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    executor = TaskExecutor(workspace, Q4WslAdapter(task),
                            command_runner=isolated_public_runner(task))
    root_id = digest({"manifest": manifest["manifest_sha256"],
                      "sequence": row["sequence"]})[:24]
    executor.admit(goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
                   scope=row["editable_paths"], permissions=["read", "edit"],
                   acceptance_path=contract_path, budget_usd=original.ALLOCATION,
                   authority_id=digest({"root": root_id, "authority": "q4-m3c"})[:32],
                   actor="q4-m3-continuation", root_id=root_id,
                   task_id=f"{row['task_id'].lower()}-{row['episode_label']}",
                   input_paths=protected,
                   experimental_dispatch=live.dispatch(row, task,
                                                       manifest["manifest_sha256"]))
    outcome = executor.run(root_id)
    terminal_failure = outcome["state"] == "blocked"
    if outcome["state"] not in {"accepted", "partial", "failed", "blocked"}:
        raise ContinuationError("root outcome is nonterminal or uncertain")
    attempts = [project_attempt(item, row, allow_failure=terminal_failure)
                for item in outcome["attempts"]]
    if not attempts or any(not item["terminal"] or not item["writer_stopped"]
                           for item in attempts):
        raise ContinuationError("episode lacks settled terminal attempts")
    if terminal_failure and (attempts[-1]["status"] != "failed"
                             or not attempts[-1]["identity_reconciled"]):
        raise ContinuationError("terminal failure identity is ambiguous")
    root_state = "failed" if terminal_failure else outcome["state"]
    executable, quality = live.live_grade(row["task_id"], rubric, workspace,
                                          root_state,
                                          attempts[-1]["evaluation_report"])
    snapshot = preserve(row, workspace)
    return {"task_id": row["task_id"],
            "episode_label": row["episode_label"], "root_id": root_id,
            "root_state": root_state, "terminal_failure": terminal_failure,
            "failure_reason": ("provider-terminal-failure" if terminal_failure
                               else None),
            "budget": outcome["budget"], "attempts": attempts,
            "executable_grade": executable, "quality_v2": quality,
            "snapshot": snapshot, "workspace": str(workspace),
            "protected_sha256": {name: sha(workspace / name)
                                 for name in protected}}


def run_campaign() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate(manifest)
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    validate_approval(manifest, approval)
    prior, _, _, inherited = predecessor()
    if RUN.exists():
        raise ContinuationError("continuation run exists; no replay")
    RUN.mkdir(mode=0o700)
    state = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "predecessor_manifest_sha256": prior["manifest_sha256"],
             "status": "running",
             "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(
                 timespec="seconds"),
             "rows": [{"sequence": index + 1, "task_id": row["task_id"],
                       "episode_label": row["episode_label"],
                       "state": "inherited-graded", "episode": row}
                      for index, row in enumerate(inherited)],
             "next_sequence": FIRST_SEQUENCE,
             "total_cost_usd": manifest["cost"]["prior_spent_usd"],
             "total_provider_calls": manifest["cost"]["prior_provider_calls"]}
    save(RUN / "campaign.json", state)
    linux = live.linux_root()
    for row in manifest["rows"]:
        validate(manifest)
        validate_approval(manifest, approval)
        new_cost = state["total_cost_usd"] - manifest["cost"]["prior_spent_usd"]
        new_calls = state["total_provider_calls"] - manifest["cost"]["prior_provider_calls"]
        if new_cost >= NEW_MAXIMUM_USD or new_calls >= NEW_MAXIMUM_CALLS:
            state.update(status="blocked", stop_reason="continuation allocation exhausted")
            save(RUN / "campaign.json", state)
            return state
        item = {"sequence": row["sequence"], "task_id": row["task_id"],
                "episode_label": row["episode_label"],
                "state": "provider-call-may-start"}
        state["rows"].append(item)
        save(RUN / "campaign.json", state)
        command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
                   "python3", "-B", f"{linux}/tools/worker_q4_screen_continue.py",
                   "--episode", "--repo", linux, "--sequence", str(row["sequence"]),
                   "--manifest", f"{linux}/{MANIFEST.relative_to(ROOT).as_posix()}",
                   "--approval", f"{linux}/{APPROVAL.relative_to(ROOT).as_posix()}"]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=7200)
            result = json.loads(process.stdout.strip())
            if process.returncode or result.get("result") != "COMPLETE":
                raise ContinuationError(result.get("error_type", "episode incomplete"))
            receipt = result["episode"]
            live.validate_receipt(row, receipt)
        except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired,
                ContinuationError) as exc:
            item.update(state="uncertain", failure_type=type(exc).__name__)
            state.update(status="blocked", stop_reason="uncertain continuation episode")
            save(RUN / "campaign.json", state)
            return state
        item.update(state="graded", episode=receipt)
        state["total_cost_usd"] += receipt["budget"]["spent_usd"]
        state["total_provider_calls"] += len(receipt["attempts"])
        state["next_sequence"] = row["sequence"] + 1
        save(RUN / "campaign.json", state)
    state.update(status="complete",
                 completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(
                     timespec="seconds"))
    save(RUN / "campaign.json", state)
    analysis_state = {"rows": [{"state": "graded", "episode": row["episode"]}
                               for row in state["rows"]]}
    decision = live.analyse(analysis_state, manifest)
    save(RUN / "decision.json", decision)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--record-standing-approval", action="store_true")
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--run", action="store_true")
    actions.add_argument("--episode", action="store_true")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--sequence", type=int)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args()
    try:
        if args.prepare:
            if MANIFEST.exists():
                raise ContinuationError("continuation manifest already exists")
            value = build_manifest(dt.datetime.now(dt.timezone.utc).date().isoformat(),
                                   sha(NOTICE))
            MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
            print(f"PASS: Q4 M3 continuation {value['manifest_sha256']}")
        elif args.record_standing_approval:
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            validate(value)
            if APPROVAL.exists():
                raise ContinuationError("continuation approval exists")
            approval = {"schema_version": 1, "decision": "approved",
                        "manifest_sha256": value["manifest_sha256"],
                        "maximum_new_usd": NEW_MAXIMUM_USD,
                        "maximum_new_provider_calls": NEW_MAXIMUM_CALLS,
                        "spend_notice_sha256": value["spend_notice_sha256"],
                        "credential_method": value["credential_method"],
                        "approved_by": "operator-standing-through-Q4-2026-09-25",
                        "approved_at": dt.datetime.now(dt.timezone.utc).isoformat(
                            timespec="seconds")}
            APPROVAL.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
            print(f"PASS: Q4 M3 continuation {value['manifest_sha256']}")
        elif args.check:
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            validate(value)
            validate_approval(value, json.loads(APPROVAL.read_text(encoding="utf-8")))
            print(f"PASS: Q4 M3 continuation {value['manifest_sha256']}")
        elif args.run:
            state = run_campaign()
            print(f"Q4 M3 continuation {state['status']}; {len(state['rows'])} rows")
            return 0 if state["status"] == "complete" else 2
        else:
            if not all((args.repo, args.sequence, args.manifest, args.approval)):
                raise ContinuationError("episode arguments are incomplete")
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            approval = json.loads(args.approval.read_text(encoding="utf-8"))
            validate_approval(manifest, approval)
            row = next(item for item in manifest["rows"]
                       if item["sequence"] == args.sequence)
            result = episode(args.repo, row, manifest)
            print(json.dumps({"result": "COMPLETE", "episode": result},
                             sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired, StopIteration) as exc:
        if args.episode:
            print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        else:
            print(f"BLOCKED: Q4 M3 continuation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
