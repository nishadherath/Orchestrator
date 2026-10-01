#!/usr/bin/env python3
"""Run the frozen Q4U canary with durable intents and no automatic replay.

Windows coordinates the campaign. Each WSL root episode is a separate Python
process, which confines the Q4U experimental executor shim to that episode.
Only the public actor inventory enters a worker namespace; hidden evaluators
run afterward in a private root-owned directory.
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

import worker_q4s_admission as journal
from worker_adapter import digest
from worker_q4u_canary_manifest import (ALLOCATION, OUTPUT as MANIFEST,
                                        ROOT, SOURCES, validate as manifest_validate)
from worker_q4u_contract import build as contract
from worker_q4u_grade import grade as hidden_grade


SOURCE = "tools/worker_q4u_canary_live.py"
APPROVAL = ROOT / "test/results/2026-09-26-worker-q4u-u3-canary-approval.json"
RUN = ROOT / "test/results/2026-09-26-worker-q4u-u3-canary-run"
RUNTIME = Path("/opt/orchestrator-worker-runtime")
CLI = RUNTIME / "bin/claude"
LAUNCHER = RUNTIME / "bin/worker-wsl-namespace-q4u"
SCHEMA = RUNTIME / "q4u-report-schema.json"
LOADER = RUNTIME / "worker_wsl_q4u.py"
Q1 = RUNTIME / "worker_wsl_q1.py"


class CanaryError(RuntimeError):
    """A source, authorisation, actor, or accounting gate cannot be proven."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approval(manifest: dict) -> None:
    if APPROVAL.is_symlink() or not APPROVAL.is_file():
        raise CanaryError("Q4U canary approval is missing or redirected")
    value = json.loads(APPROVAL.read_text(encoding="utf-8"))
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_authorised_usd": 40.0,
                "maximum_provider_calls": 30,
                "credential_method": "claude-code-wsl-subscription",
                "authority": "operator-standing-paid-calls-approved"}
    if (set(value) != set(expected) | {"approved_at_utc"}
            or any(value.get(key) != item for key, item in expected.items())
            or not isinstance(value.get("approved_at_utc"), str)
            or not value["approved_at_utc"].strip()):
        raise CanaryError("Q4U approval is not bound to the frozen manifest")


def frozen() -> dict:
    value = manifest_validate()
    approval(value)
    if (value["date_utc"] != dt.datetime.now(dt.timezone.utc).date().isoformat()
            or len(value["rows"]) != 10
            or value["maximum_provider_calls"] != 30
            or value["maximum_allocation_usd"] != 40.0):
        raise CanaryError("Q4U canary freeze is stale or outside its bounds")
    return value


def linux_root() -> str:
    process = subprocess.run(
        ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "wslpath", "-a",
         ROOT.as_posix()], capture_output=True, text=True, timeout=30)
    if process.returncode or not process.stdout.strip().startswith("/mnt/"):
        raise CanaryError("repository is unavailable from WSL root")
    return process.stdout.strip()


def wsl_probe(linux: str, script: str) -> dict:
    process = subprocess.run(
        ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "python3",
         "-B", f"{linux}/tools/{script}", "--repo", linux],
        capture_output=True, text=True, timeout=180)
    if process.returncode:
        raise CanaryError(f"provider-free WSL probe failed: {script}")
    value = json.loads(process.stdout)
    if (value.get("result") != "PASS" or value.get("provider_calls") != 0
            or value.get("provider_cost_usd") != 0):
        raise CanaryError(f"provider-free WSL probe is incomplete: {script}")
    return value


def host_proof(repo: Path, manifest: dict) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0 or repo.resolve() != ROOT.resolve():
        raise CanaryError("Q4U host proof requires the exact WSL root repository")
    expected = manifest["source_sha256"]
    if (set(expected) != set(SOURCES)
            or any(sha(ROOT / name) != value for name, value in expected.items())
            or sha(CLI) != manifest["runtime_cli_sha256"]
            or sha(LAUNCHER) != expected["tools/worker_wsl_namespace_q4u.sh"]
            or sha(LOADER) != expected["tools/worker_wsl_q4u.py"]
            or sha(Q1) != expected["tools/worker_wsl_q1.py"]
            or sha(SCHEMA) != manifest["runtime_schema_sha256"]):
        raise CanaryError("Q4U runtime or source differs from frozen manifest")
    value = {"schema_version": 1, "result": "PASS",
             "manifest_sha256": manifest["manifest_sha256"],
             "source_sha256": expected,
             "runtime_cli_sha256": manifest["runtime_cli_sha256"],
             "runtime_launcher_sha256": sha(LAUNCHER),
             "runtime_schema_sha256": sha(SCHEMA),
             "provider_calls": 0, "provider_cost_usd": 0}
    return {**value, "proof_sha256": digest(value)}


def preflight(linux: str, manifest: dict) -> dict:
    process = subprocess.run(
        ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "python3", "-B",
         f"{linux}/{SOURCE}", "--host-proof", "--repo", linux],
        capture_output=True, text=True, timeout=120)
    if process.returncode:
        raise CanaryError("Q4U source or runtime host proof failed")
    host = json.loads(process.stdout)
    if (host.get("result") != "PASS"
            or host.get("manifest_sha256") != manifest["manifest_sha256"]
            or host.get("proof_sha256") != digest({
                key: item for key, item in host.items() if key != "proof_sha256"})):
        raise CanaryError("Q4U host proof is incomplete")
    auth = wsl_probe(linux, "worker_wsl_q4u_auth_probe.py")
    probe = wsl_probe(linux, "worker_wsl_q4u_probe.py")
    value = {"schema_version": 1, "result": "PASS",
             "manifest_sha256": manifest["manifest_sha256"],
             "source_sha256": manifest["source_sha256"],
             "historical_runtime": host, "auth": auth, "probe": probe}
    return {**value, "evidence_sha256": digest(value)}


def _score(row: dict, task: dict, workspace: Path,
           root_state: str, report_record: dict) -> tuple[dict, dict]:
    from worker_wsl_q4u_adapter import isolated_public_runner

    hidden = hidden_grade(row["task_id"], workspace)
    public = isolated_public_runner(task)(
        ["python3", "-B", "public_check.py"], cwd=workspace,
        capture_output=True, timeout=30, shell=False)
    if public.returncode not in {0, 1}:
        raise CanaryError("isolated public check did not finish normally")
    report_present = report_record.get("observability") == "present"
    claimed_complete = ((report_record.get("report") or {}).get("status") == "completed"
                        if report_present else False)
    hidden_accepted = (hidden["score"] == 100 and public.returncode == 0
                       and root_state == "accepted" and report_present)
    quality = {"schema_version": 2, "quality": hidden["score"],
               "hidden_accepted": hidden_accepted,
               "false_success": root_state == "accepted" and not hidden_accepted,
               "unsupported_completion": claimed_complete and hidden["score"] < 100,
               "critical_error": False, "inconclusive": False,
               "report_observability": report_record.get("observability")}
    executable = {"schema_version": 1, "task_id": row["task_id"],
                  "hidden_score": hidden["score"], "hidden_grade_sha256": hidden["grade_sha256"],
                  "public_pass": public.returncode == 0,
                  "public_isolation_sha256": public.isolation_evidence["sha256"],
                  "hidden_grade": hidden}
    return executable, quality


def _preserve(row: dict, workspace: Path) -> dict:
    target = RUN / "patches" / f"{row['sequence']:02d}-{row['task_id'].lower()}-{row['arm']}"
    if target.exists() or target.is_symlink():
        raise CanaryError("Q4U patch snapshot already exists")
    target.mkdir(parents=True)
    hashes = {}
    for relative in row["editable_paths"]:
        source = workspace / relative
        if source.is_symlink() or not source.is_file():
            raise CanaryError("Q4U editable output is missing or unsafe")
        data = source.read_bytes()
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        hashes[relative] = hashlib.sha256(data).hexdigest()
    value = {"schema_version": 1, "editable_sha256": hashes,
             "directory": str(target.relative_to(RUN)), "protected_preserved": False}
    return {**value, "snapshot_sha256": digest(value)}


def episode(repo: Path, sequence: int) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0:
        raise CanaryError("Q4U episode requires WSL root")
    manifest = frozen()
    host_proof(repo, manifest)
    if not 1 <= sequence <= len(manifest["rows"]):
        raise CanaryError("Q4U sequence is outside frozen campaign")
    row = manifest["rows"][sequence - 1]
    state = journal._read(RUN / "campaign.json")
    if (state.get("status") != "running"
            or state.get("manifest_sha256") != manifest["manifest_sha256"]
            or len(state.get("rows", [])) != sequence
            or state["rows"][-1] != {"sequence": sequence,
                                    "task_id": row["task_id"],
                                    "episode_label": row["arm"],
                                    "state": "provider-call-may-start"}):
        raise CanaryError("Q4U episode has no exact persisted provider intent")
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q4u_adapter import Q4UWslAdapter, isolated_public_runner
    from worker_q4u_executor import Q4UTaskExecutor

    CredentialStore().inspect()
    folder = ROOT / "test/fixtures/worker_q4u_public" / row["task_id"]
    task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
    public = json.loads((folder / "public_assessment.json").read_text(
        encoding="utf-8"))
    command = contract(row["task_id"])
    if (task["task_sha256"] != row["task_sha256"]
            or task["evaluator_zip_sha256"] != row["evaluator_zip_sha256"]
            or task["actor_files"] != row["actor_files"]
            or task["editable_paths"] != row["editable_paths"]
            or public["assessment"]["assessment_sha256"] != row["public_assessment_sha256"]
            or digest(command) != row["contract_sha256"]):
        raise CanaryError("Q4U task or assessment differs from frozen row")
    workspace = SEEDS / f"q4u-{manifest['manifest_sha256'][:12]}-{sequence:02d}"
    if workspace.exists() or workspace.is_symlink():
        raise CanaryError("Q4U actor workspace already exists; no replay")
    workspace.mkdir(mode=0o700)
    for relative, expected in row["actor_files"].items():
        data = (folder / "actor" / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise CanaryError("Q4U actor source differs from frozen row")
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    protected = {name: value for name, value in row["actor_files"].items()
                 if name not in row["editable_paths"]}
    contract_path = workspace / ".claude/q4u-acceptance.json"
    contract_path.parent.mkdir()
    contract_path.write_text(json.dumps(command, sort_keys=True), encoding="utf-8")
    executor = Q4UTaskExecutor(workspace, Q4UWslAdapter(task),
                               command_runner=isolated_public_runner(task))
    root_id = digest({"manifest": manifest["manifest_sha256"],
                      "sequence": sequence})[:24]
    spec = {"schema_version": 3, "arm": row["arm"],
            "manifest_sha256": manifest["manifest_sha256"],
            "public_assessment": public, "cost_ceiling_usd": ALLOCATION}
    executor.admit(goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
                   scope=row["editable_paths"], permissions=["read", "edit"],
                   acceptance_path=contract_path, budget_usd=ALLOCATION,
                   authority_id=digest({"root": root_id, "authority": "q4u"})[:32],
                   actor="q4u-public", root_id=root_id,
                   task_id=f"{row['task_id'].lower()}-{row['arm']}",
                   input_paths=sorted(protected), experimental_dispatch=spec)
    outcome = executor.run(root_id)
    if outcome["experimental_policy"]["ladder"] != row["ladder"]:
        raise CanaryError("Q4U executed ladder differs from frozen row")
    settled = journal.settle_stopped_patch(
        outcome, workspace, protected,
        lambda path, root_state, report: _score(row, task, path, root_state, report),
        lambda path: _preserve(row, path))
    attempts = []
    for attempt in outcome["attempts"]:
        receipt = attempt.get("receipt") or {}
        if attempt.get("receipt_digest") != digest(receipt):
            raise CanaryError("Q4U TaskExecutor receipt digest differs")
        boundary = receipt.get("command_contract", {}).get("q4u_boundary", {})
        attempts.append({"sequence": attempt["sequence"],
                         "invocation_id": attempt["invocation_id"],
                         "requested_cell": attempt["requested_cell"],
                         "actual_model": receipt.get("actual_model"),
                         "identity_valid": receipt.get("identity_valid"),
                         "status": receipt.get("status"),
                         "terminal": receipt.get("terminal"),
                         "writer_stopped": receipt.get("writer_stopped"),
                         "cost_usd": receipt.get("cost_usd"),
                         "wall_clock_s": receipt.get("wall_clock_s"),
                         "usage": receipt.get("usage"),
                         "verification": (attempt.get("verification") or {}).get("status"),
                         "boundary": boundary,
                         "evaluation_report": receipt.get("evaluation_report") or {},
                         "evaluation_report_digest": receipt.get("evaluation_report_digest"),
                         "evaluation_transport": receipt.get("evaluation_transport") or {},
                         "q4t_diagnostics": receipt.get("q4t_diagnostics") or {},
                         "receipt_digest": attempt["receipt_digest"]})
    value = {"schema_version": 1, "sequence": sequence,
             "task_id": row["task_id"], "episode_label": row["arm"],
             "manifest_sha256": manifest["manifest_sha256"],
             "root_id": root_id, "root_state": outcome["state"],
             "attempts": attempts, "budget": outcome["budget"],
             "workspace": str(workspace), "protected_integrity": True,
             **settled}
    result = {**value, "evidence_sha256": digest(value)}
    (workspace / "q4u-u3-receipt.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def _adjudicate(row: dict, item: dict, manifest: dict) -> str | None:
    if (item.get("evidence_sha256") != digest({
            key: value for key, value in item.items() if key != "evidence_sha256"})
            or item.get("manifest_sha256") != manifest["manifest_sha256"]
            or item.get("sequence") != row["sequence"]
            or item.get("task_id") != row["task_id"]
            or item.get("episode_label") != row["arm"]
            or item.get("protected_integrity") is not True
            or item.get("settlement", {}).get("cost_settled") is not True):
        raise CanaryError("Q4U episode identity or settlement differs")
    attempts = item.get("attempts") or []
    charge = item["settlement"]["charged_usd"]
    if (not 1 <= len(attempts) <= 3
            or [attempt["requested_cell"] for attempt in attempts]
               != row["ladder"][:len(attempts)]
            or any(attempt.get("identity_valid") is not True
                   or attempt.get("terminal") is not True
                   or attempt.get("writer_stopped") is not True
                   or not attempt.get("boundary")
                   or type(attempt.get("cost_usd")) not in (int, float)
                   for attempt in attempts)
            or not math.isclose(sum(x["cost_usd"] for x in attempts), charge,
                                abs_tol=1e-8)):
        return "Q4U attempt identity, writer, boundary or accounting is uncertain"
    if charge > row["episode_maximum_usd"]:
        return "Q4U episode allocation overrun"
    if any((x["evaluation_report"] or {}).get("observability") != "present"
           for x in attempts):
        return "Q4U structured report failure; preserve settled episode"
    if item["quality_v2"]["false_success"]:
        # A false success is a measured outcome; keep the paired evidence but
        # prevent any later promotion from this canary.
        return None
    return None


def _stop(reason: str, *, uncertain: bool) -> dict:
    path = RUN / "campaign.json"
    state = journal._read(path)
    if uncertain and state["rows"] and state["rows"][-1]["state"] == "provider-call-may-start":
        state["rows"][-1]["state"] = "uncertain"
    state.update(status="blocked", stop_reason=reason)
    journal._write(path, state)
    return journal._read(path)


def analyse(state: dict, manifest: dict) -> dict:
    rows = [item["episode"] for item in state["rows"] if item["state"] == "graded"]
    by_task = {}
    for item in rows:
        by_task.setdefault(item["task_id"], {})[item["episode_label"]] = item
    pairs = []
    for task_id in sorted(by_task):
        arms = by_task[task_id]
        baseline = arms.get("b0")
        if baseline is None:
            continue
        for policy in ("cross_component_medium", "coverage_repair"):
            other = arms.get(policy)
            if other is None:
                continue
            pairs.append({"task_id": task_id, "policy": policy,
                          "quality_delta": other["quality_v2"]["quality"] -
                                           baseline["quality_v2"]["quality"],
                          "false_success_delta": int(other["quality_v2"]["false_success"]) -
                                                 int(baseline["quality_v2"]["false_success"]),
                          "cost_delta_usd": other["settlement"]["charged_usd"] -
                                            baseline["settlement"]["charged_usd"],
                          "latency_delta_s": sum(x["wall_clock_s"] for x in other["attempts"]) -
                                             sum(x["wall_clock_s"] for x in baseline["attempts"])})
    complete = state["status"] == "complete" and len(rows) == len(manifest["rows"])
    candidate_gain = any(p["quality_delta"] >= 10 for p in pairs)
    candidate_harm = any(p["quality_delta"] < 0 or p["false_success_delta"] > 0
                         for p in pairs)
    value = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "status": "complete" if complete else "incomplete",
             "settled_episodes": len(rows),
             "provider_calls": state["total_provider_calls"],
             "charged_usd": state["total_cost_usd"],
             "pairs": pairs,
             "policy_decision": ("retain-b0-incomplete" if not complete else
                                 "retain-b0-observed-harm" if candidate_harm else
                                 "exploratory-gain-requires-separate-qualification"
                                 if candidate_gain else "retain-b0-no-clear-gain"),
             "qualification_authority": False,
             "stop_reason": state.get("stop_reason")}
    return {**value, "analysis_sha256": digest(value)}


def campaign() -> dict:
    if os.name != "nt":
        raise CanaryError("Q4U campaign coordinator requires Windows")
    manifest = frozen()
    if RUN.exists() or RUN.is_symlink():
        raise CanaryError("Q4U campaign path already exists; no automatic replay")
    linux = linux_root()
    journal.start_campaign(RUN, manifest["manifest_sha256"],
                           lambda: preflight(linux, manifest))
    for row in manifest["rows"]:
        manifest = frozen()
        state = journal._read(RUN / "campaign.json")
        if (state["total_provider_calls"] >= manifest["maximum_provider_calls"]
                or state["total_cost_usd"] >= manifest["maximum_allocation_usd"]):
            return _stop("Q4U allocation exhausted", uncertain=False)
        try:
            preflight(linux, manifest)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError,
                subprocess.TimeoutExpired) as exc:
            return _stop(f"Q4U pre-dispatch proof failed: {type(exc).__name__}",
                         uncertain=False)
        journal.mark_intent(RUN, row["sequence"], row["task_id"], row["arm"])
        try:
            process = subprocess.run(
                ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "python3",
                 "-B", f"{linux}/{SOURCE}", "--episode", "--repo", linux,
                 "--sequence", str(row["sequence"])],
                capture_output=True, text=True, timeout=7200)
            result = json.loads(process.stdout)
            if process.returncode or result.get("result") != "COMPLETE":
                raise CanaryError("Q4U WSL episode did not return a settled receipt")
            item = result["episode"]
            stop = _adjudicate(row, item, manifest)
            state = journal._read(RUN / "campaign.json")
            intent = state["rows"][-1]
            if (intent["state"] != "provider-call-may-start"
                    or intent["sequence"] != row["sequence"]):
                raise CanaryError("Q4U persisted intent changed before settlement")
            intent.update(state="graded", episode=item)
            state["total_cost_usd"] += item["settlement"]["charged_usd"]
            state["total_provider_calls"] += item["settlement"]["provider_calls"]
            if (state["total_cost_usd"] > manifest["maximum_allocation_usd"]
                    or state["total_provider_calls"] > manifest["maximum_provider_calls"]):
                stop = "Q4U campaign allocation or call ceiling exceeded"
            if stop:
                state.update(status="blocked", stop_reason=stop)
            journal._write(RUN / "campaign.json", state)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError,
                subprocess.TimeoutExpired) as exc:
            return _stop(f"Q4U episode {row['sequence']} uncertain: "
                         f"{type(exc).__name__}", uncertain=True)
        if state["status"] != "running":
            result = analyse(state, manifest)
            journal._write(RUN / "analysis.json", result)
            return state
    state = journal._read(RUN / "campaign.json")
    state.update(status="complete",
                 completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(
                     timespec="seconds"))
    journal._write(RUN / "campaign.json", state)
    journal._write(RUN / "analysis.json", analyse(state, manifest))
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--host-proof", action="store_true")
    mode.add_argument("--episode", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--sequence", type=int)
    args = parser.parse_args()
    try:
        if args.host_proof:
            result = host_proof(args.repo, frozen())
        elif args.episode:
            result = {"result": "COMPLETE", "episode": episode(args.repo, args.sequence)}
        else:
            state = campaign()
            result = {"result": "COMPLETE" if state["status"] == "complete" else "BLOCKED",
                      "status": state["status"], "settled_episodes": sum(
                          row["state"] == "graded" for row in state["rows"]),
                      "provider_calls": state["total_provider_calls"],
                      "charged_usd": state["total_cost_usd"],
                      "stop_reason": state.get("stop_reason")}
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"result": "BLOCKED", "error_type": type(exc).__name__,
                          "reason": str(exc)[:300]}, sort_keys=True))
        return 2
    return 0 if result.get("result") in {"PASS", "COMPLETE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
