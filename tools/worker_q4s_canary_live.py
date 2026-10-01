#!/usr/bin/env python3
"""Freeze and run the two-call Q4S transport canary without replay.

The S2 manifest binds the task and transport. This stage manifest additionally
binds the paid driver, which did not exist when S2 was frozen. A persisted
intent precedes each call; ambiguous outcomes remain blocked for reconciliation.
"""
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
import worker_q4s_admission as journal
import worker_q4s_screen as screen
from worker_adapter import WorkerRequest, digest
from worker_q4r_structured import report_schema


ROOT = screen.ROOT
MANIFEST = ROOT / "test/results/2026-09-26-worker-q4s-s3-manifest.json"
APPROVAL = ROOT / "test/results/2026-09-26-worker-q4s-s3-approval.json"
RUN = ROOT / "test/results/2026-09-26-worker-q4s-s3-run"
SOURCE = "tools/worker_q4s_canary_live.py"
CELLS = ("worker-sonnet-low", "worker-sonnet-medium")
ALLOCATION = 3.0


class CanaryError(RuntimeError):
    """The canary cannot start or advance under its frozen contract."""


def frozen_parent() -> dict:
    value = json.loads(screen.MANIFEST.read_text(encoding="utf-8"))
    if value != screen.build_manifest(value["date_utc"]):
        raise CanaryError("S2 manifest differs from current host or source")
    return value


def build_manifest() -> dict:
    parent = frozen_parent()
    value = {
        "schema_version": 1,
        "profile": "worker-q4s-s3-head-only-canary",
        "parent_manifest_sha256": parent["manifest_sha256"],
        "canary_task_sha256": parent["canary"]["task_sha256"],
        "spend_notice_sha256": parent["spend_notice_sha256"],
        "source_sha256": {SOURCE: screen.sha(ROOT / SOURCE)},
        "cells": list(CELLS),
        "episode_allocation_usd": ALLOCATION,
        "maximum_allocation_usd": 2 * ALLOCATION,
        "maximum_provider_calls": 2,
        "repair_cells": [],
        "stop_on_failed_or_uncertain_canary": True,
        "authorisation": parent["authorisation"],
    }
    return {**value, "manifest_sha256": digest(value)}


def validate_manifest() -> tuple[dict, dict]:
    parent = frozen_parent()
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if value != build_manifest():
        raise CanaryError("S3 manifest differs from frozen inputs")
    if (value["parent_manifest_sha256"] != parent["manifest_sha256"]
            or value["cells"] != list(CELLS)
            or value["maximum_provider_calls"] != 2
            or value["maximum_allocation_usd"] != 6.0
            or value["repair_cells"] != []):
        raise CanaryError("S3 canary scope changed")
    return parent, value


def validate_approval(manifest: dict) -> None:
    if APPROVAL.is_symlink():
        raise CanaryError("S3 approval is redirected")
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_authorised_usd": 6.0,
                "maximum_provider_calls": 2,
                "credential_method": "claude-code-wsl-subscription"}
    if ({key: approval.get(key) for key in expected} != expected
            or set(approval) != set(expected) | {"approved_at_utc"}
            or not isinstance(approval.get("approved_at_utc"), str)
            or not approval["approved_at_utc"].strip()):
        raise CanaryError("S3 approval is not bound to this exact manifest")


def linux_root() -> str:
    process = subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root",
                              "--", "wslpath", "-a", ROOT.as_posix()],
                             capture_output=True, text=True, timeout=30)
    if process.returncode or not process.stdout.strip().startswith("/mnt/"):
        raise CanaryError("repository is unavailable to WSL root")
    return process.stdout.strip()


def provider_free_probe(linux: str, script: str) -> dict:
    process = subprocess.run(
        ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "python3", "-B",
         f"{linux}/tools/{script}", "--repo", linux],
        capture_output=True, text=True, timeout=180)
    if process.returncode:
        raise CanaryError(f"Q4S provider-free preflight failed: {script}")
    value = json.loads(process.stdout)
    if (value.get("result") != "PASS" or value.get("provider_calls") != 0
            or value.get("provider_cost_usd") != 0):
        raise CanaryError(f"Q4S provider-free preflight is incomplete: {script}")
    return value


def preflight(parent: dict, stage: dict, linux: str) -> dict:
    auth = provider_free_probe(linux, "worker_wsl_q4s_auth_probe.py")
    probe = provider_free_probe(linux, "worker_wsl_q4s_probe.py")
    proof = {"schema_version": 1, "result": "PASS",
             "parent_manifest_sha256": parent["manifest_sha256"],
             "stage_manifest_sha256": stage["manifest_sha256"],
             "source_sha256": {**parent["source_sha256"],
                               **stage["source_sha256"]},
             "auth": auth, "probe": probe}
    return {**proof, "evidence_sha256": digest(proof)}


def stop_uncertain(reason: str) -> dict:
    state_path = RUN / "campaign.json"
    state = journal._read(state_path)
    state.update(status="blocked", stop_reason=reason)
    journal._write(state_path, state)
    return journal._read(state_path)


def validate_episode(episode: dict, cell: str, parent: dict,
                     stage: dict) -> None:
    receipt = episode.get("receipt") or {}
    settlement = episode.get("settlement") or {}
    boundary = receipt.get("boundary") or {}
    transport = receipt.get("transport") or {}
    expected_model = model_registry.resolve_cell(cell)["cli_model"]
    amount = settlement.get("charged_usd")
    if (episode.get("task_id") != "Q4S-CANARY"
            or episode.get("episode_label") != cell
            or episode.get("parent_manifest_sha256") != parent["manifest_sha256"]
            or episode.get("stage_manifest_sha256") != stage["manifest_sha256"]
            or receipt.get("requested_cell") != cell
            or receipt.get("terminal") is not True
            or receipt.get("writer_stopped") is not True
            or episode.get("protected_sha256") != {
                key: value for key, value in parent["canary"]["actor_files"].items()
                if key not in parent["canary"]["editable_paths"]}
            or settlement.get("writer_stopped") is not True
            or settlement.get("cost_settled") is not True
            or settlement.get("provider_calls") != 1
            or type(amount) not in (int, float)
            or not math.isfinite(amount) or amount < 0
            or not isinstance(episode.get("snapshot"), dict)
            or not isinstance(episode.get("executable_grade"), dict)
            or not isinstance(episode.get("quality_v2"), dict)):
        raise CanaryError("S3 terminal receipt or settled charge is invalid")
    changed = boundary.get("changed_paths")
    eligible = (receipt.get("actual_model") == expected_model
                and receipt.get("root_models") == [expected_model]
                and receipt.get("status") == "completed"
                and receipt.get("identity_valid") is True
                and receipt.get("report_observability") == "present"
                and transport.get("mode") == "claude-code-json-schema-v1"
                and transport.get("schema_sha256") == digest(report_schema())
                and transport.get("structured_output_present") is True
                and isinstance(changed, list) and bool(changed)
                and set(changed).issubset(parent["canary"]["editable_paths"])
                and isinstance(boundary.get("q1_record_sha256"), str)
                and len(boundary["q1_record_sha256"]) == 64
                and isinstance(boundary.get("q1_spec_sha256"), str)
                and len(boundary["q1_spec_sha256"]) == 64
                and amount <= ALLOCATION
                and episode["executable_grade"].get("isolated") is True)
    if episode.get("qualification_eligible") is not eligible:
        raise CanaryError("S3 terminal qualification differs from its evidence")


def run_campaign() -> dict:
    parent, stage = validate_manifest()
    validate_approval(stage)
    if RUN.exists() or RUN.is_symlink():
        raise CanaryError("S3 run already exists; no automatic replay")
    linux = linux_root()
    journal.start_campaign(RUN, stage["manifest_sha256"],
                           lambda: preflight(parent, stage, linux))
    for sequence, cell in enumerate(CELLS, 1):
        parent, stage = validate_manifest()
        validate_approval(stage)
        journal.mark_intent(RUN, sequence, "Q4S-CANARY", cell)
        command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
                   "python3", "-B", f"{linux}/{SOURCE}", "--episode",
                   "--repo", linux, "--sequence", str(sequence)]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=3600)
            result = json.loads(process.stdout)
            if process.returncode or result.get("result") != "COMPLETE":
                raise CanaryError("WSL episode did not return a settled receipt")
            episode = result["episode"]
            validate_episode(episode, cell, parent, stage)
            state = journal.settle_episode(RUN, episode)
        except (OSError, ValueError, TypeError, KeyError, CanaryError,
                journal.Q4SAdmissionError, subprocess.TimeoutExpired) as exc:
            return stop_uncertain(f"episode {sequence}: {type(exc).__name__}")
        if state["status"] != "running":
            return state
    state = journal._read(RUN / "campaign.json")
    if (len(state["rows"]) != 2 or state["total_provider_calls"] != 2
            or state["total_cost_usd"] > 6.0
            or any(row["state"] != "graded" for row in state["rows"])):
        return stop_uncertain("S3 campaign accounting differs")
    state.update(status="complete", completed_at_utc=dt.datetime.now(
        dt.timezone.utc).isoformat(timespec="seconds"))
    journal._write(RUN / "campaign.json", state)
    return journal._read(RUN / "campaign.json")


def run_episode(repo: Path, sequence: int) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0 or sequence not in (1, 2):
        raise CanaryError("S3 episode requires WSL root and a frozen sequence")
    parent, stage = validate_manifest()
    validate_approval(stage)
    state = journal._read(RUN / "campaign.json")
    cell = CELLS[sequence - 1]
    if (state.get("status") != "running"
            or state.get("manifest_sha256") != stage["manifest_sha256"]
            or len(state.get("rows", [])) != sequence
            or state["rows"][-1] != {
                "sequence": sequence, "task_id": "Q4S-CANARY",
                "episode_label": cell, "state": "provider-call-may-start"}):
        raise CanaryError("S3 episode has no exact persisted provider-call intent")
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q3_adapter import isolated_public_runner
    from worker_wsl_q4s_adapter import Q4SWslAdapter

    CredentialStore().inspect()
    canary = parent["canary"]
    task = {**canary, "id": "Q4S-CANARY"}
    workspace = SEEDS / f"q4s-{stage['manifest_sha256'][:12]}-s3-{sequence}"
    if workspace.exists() or workspace.is_symlink():
        raise CanaryError("canary actor already exists; no replay")
    workspace.mkdir(mode=0o700)
    source = repo / "test/fixtures/worker_q4s_canary/actor"
    for relative, expected in canary["actor_files"].items():
        data = (source / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise CanaryError("canary source differs from parent manifest")
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    protected = {key: value for key, value in canary["actor_files"].items()
                 if key not in canary["editable_paths"]}
    intent = digest({"stage": stage["manifest_sha256"], "sequence": sequence})
    request = WorkerRequest(
        workspace, (workspace / "ISSUE.md").read_text(encoding="utf-8"),
        tuple(canary["editable_paths"]), cell, ALLOCATION,
        "Q4S S3 transport canary. One head call only; report remaining work honestly.",
        admission_token=stage["manifest_sha256"], invocation_id=intent[:32],
        revision_id=digest({"intent": intent, "kind": "revision"})[:32],
        decision_digest=digest({"intent": intent, "cell": cell}),
        intent_digest=intent)
    receipt = Q4SWslAdapter(task).run(request)
    cost = receipt.get("cost_usd")
    if (receipt.get("terminal") is not True
            or receipt.get("writer_stopped") is not True
            or type(cost) not in (int, float) or not math.isfinite(cost)
            or cost < 0):
        raise CanaryError("provider outcome or charge is uncertain")
    for relative, expected in protected.items():
        if hashlib.sha256((workspace / relative).read_bytes()).hexdigest() != expected:
            raise CanaryError("protected canary source changed")
    boundary = receipt.get("command_contract", {}).get("q4s_boundary", {})
    changed = boundary.get("changed_paths") or []
    report = receipt.get("evaluation_report") or {}
    transport = receipt.get("evaluation_transport") or {}
    public = isolated_public_runner(task)(
        ["python3", "-B", "public_check.py"], cwd=workspace,
        capture_output=True, timeout=30, shell=False)
    snapshot = {"workspace": str(workspace), "files": {
        name: hashlib.sha256((workspace / name).read_bytes()).hexdigest()
        for name in canary["editable_paths"]}}
    eligible = (receipt.get("status") == "completed" and cost <= ALLOCATION
                and receipt.get("identity_valid") is True
                and receipt.get("actual_model") == model_registry.resolve_cell(cell)[
                    "cli_model"]
                and receipt.get("root_models") == [receipt.get("actual_model")]
                and report.get("observability") == "present"
                and transport.get("mode") == "claude-code-json-schema-v1"
                and transport.get("schema_sha256") == digest(report_schema())
                and transport.get("structured_output_present") is True
                and bool(changed) and set(changed).issubset(canary["editable_paths"])
                and isinstance(boundary.get("q1_record_sha256"), str)
                and len(boundary["q1_record_sha256"]) == 64
                and isinstance(boundary.get("q1_spec_sha256"), str)
                and len(boundary["q1_spec_sha256"]) == 64
                and hasattr(public, "isolation_evidence"))
    episode = {
        "task_id": "Q4S-CANARY", "episode_label": cell,
        "parent_manifest_sha256": parent["manifest_sha256"],
        "stage_manifest_sha256": stage["manifest_sha256"],
        "settlement": {"charged_usd": cost, "provider_calls": 1,
                       "writer_stopped": True, "cost_settled": True},
        "qualification_eligible": eligible,
        "receipt": {"requested_cell": cell, "actual_model": receipt.get("actual_model"),
                    "root_models": receipt.get("root_models"),
                    "requested_effort": receipt.get("requested_effort"),
                    "identity_valid": receipt.get("identity_valid"),
                    "status": receipt.get("status"), "terminal": True,
                    "writer_stopped": True, "usage": receipt.get("usage"),
                    "report_observability": report.get("observability"),
                    "report_digest": receipt.get("evaluation_report_digest"),
                    "boundary": boundary, "transport": transport,
                    "diagnostics": receipt.get("q4s_diagnostics")},
        "report_observability": report.get("observability"),
        "protected_sha256": protected, "snapshot": snapshot,
        "executable_grade": {"public_pass": public.returncode == 0,
                             "isolated": hasattr(public, "isolation_evidence")},
        "quality_v2": {"scored": False, "reason": "transport-only-canary"},
    }
    evidence = {**episode, "evidence_sha256": digest(episode)}
    path = workspace / "q4s-s3-receipt.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return episode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--episode", action="store_true")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--sequence", type=int)
    args = parser.parse_args()
    try:
        if args.prepare:
            if MANIFEST.exists():
                raise CanaryError("S3 manifest already exists")
            MANIFEST.write_text(json.dumps(build_manifest(), indent=2,
                                           sort_keys=True) + "\n", encoding="utf-8")
            print("PASS: S3 manifest frozen")
        elif args.check:
            _, stage = validate_manifest()
            print(f"PASS: S3 manifest {stage['manifest_sha256']}")
        elif args.run:
            state = run_campaign()
            print(f"Q4S S3 {state['status']}; {len(state['rows'])} canary calls")
            return 0 if state["status"] == "complete" else 2
        else:
            if args.repo is None or args.sequence is None:
                raise CanaryError("WSL episode arguments are incomplete")
            episode = run_episode(args.repo, args.sequence)
            print(json.dumps({"result": "COMPLETE", "episode": episode},
                             sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        if args.episode:
            print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        else:
            print(f"BLOCKED: Q4S S3: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
