#!/usr/bin/env python3
"""Run the source-bound Q4T public screen with durable no-replay intents."""
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

import worker_q4s_admission as journal
import worker_q4t_canary_live as canary
import worker_q4t_screen as screen
import worker_q4t_screen_evidence as evidence
import worker_selector
from worker_adapter import digest
from worker_q4r_structured import schema_argument
from worker_q4t_policy import settled_stop_reason
from worker_q4t_public import FAMILIES, ROOT, actor_root, build, sha


SOURCE = "tools/worker_q4t_screen_live.py"
EVIDENCE_SOURCE = "tools/worker_q4t_screen_evidence.py"
MANIFEST = ROOT / "test/results/2026-09-26-worker-q4t-s3-manifest.json"
APPROVAL = ROOT / "test/results/2026-09-26-worker-q4t-s3-approval.json"
RUN = ROOT / "test/results/2026-09-26-worker-q4t-s3-run"
ALLOCATION = 4.0
MAX_USD = 72.0
MAX_CALLS = 54
LAUNCHER = Path("/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace-q4t")
SCHEMA = Path("/opt/orchestrator-worker-runtime/q4t-report-schema.json")
CLI = Path("/opt/orchestrator-worker-runtime/bin/claude")


class LiveScreenError(RuntimeError):
    """The paid screen cannot safely start, advance or settle."""


def frozen_parent() -> dict:
    parent = json.loads(screen.MANIFEST.read_text(encoding="utf-8"))
    q4s = json.loads(screen.Q4S_PARENT.read_text(encoding="utf-8"))
    c1 = json.loads(screen.C1_MANIFEST.read_text(encoding="utf-8"))
    if (parent.get("manifest_sha256") != digest({
            key: value for key, value in parent.items() if key != "manifest_sha256"})
            or q4s.get("manifest_sha256") != parent["q4s_parent_manifest_sha256"]
            or c1.get("manifest_sha256") != parent["c1_manifest_sha256"]
            or any(sha(ROOT / name) != expected for name, expected in
                   parent["source_sha256"].items())
            or sha(screen.NOTICE) != parent["spend_notice_sha256"]
            or sha(screen.Q4S_CALIBRATION) != parent["q4s_calibration_sha256"]
            or sha(screen.T07_CALIBRATION) != parent["t07_calibration_sha256"]
            or parent["rows"] != screen.screen_rows()
            or any(digest(screen.live_rubric(row)) != parent["live_rubric_sha256"][
                row["task_id"]] for row in parent["rows"])):
        raise LiveScreenError("Q4T S2 design differs from frozen source")
    return parent


def build_manifest(date_utc: str) -> dict:
    dt.date.fromisoformat(date_utc)
    parent = frozen_parent()
    value = {
        "schema_version": 1, "profile": "worker-q4t-s3-six-family-paid-screen",
        "date_utc": date_utc,
        "parent_manifest_sha256": parent["manifest_sha256"],
        "parent_rows_sha256": digest(parent["rows"]),
        "spend_notice_sha256": parent["spend_notice_sha256"],
        "source_sha256": {name: sha(ROOT / name) for name in
                          (SOURCE, EVIDENCE_SOURCE, "tools/worker_selector.py",
                           "tools/worker_q4t_canary_live.py",
                           "tools/worker_wsl_q4t_auth_probe.py",
                           "tools/worker_wsl_q4t_probe.py")},
        "runtime_cli_sha256": parent["runtime_cli_sha256"],
        "runtime_launcher_sha256": parent["runtime_launcher_sha256"],
        "runtime_schema_sha256": hashlib.sha256(
            (schema_argument().split("=", 1)[1] + "\n").encode()).hexdigest(),
        "transport_mode": parent["transport_mode"],
        "structured_retry_limit": parent["structured_retry_limit"],
        "episode_count": len(parent["rows"]), "family_count": len(FAMILIES),
        "episode_allocation_usd": ALLOCATION,
        "maximum_allocation_usd": MAX_USD,
        "maximum_provider_calls": MAX_CALLS,
        "selection_rules": {**parent["selection_rules"],
                            "upstream_only_gain_required": True},
        "stop_policy": parent["stop_policy"],
        "authorisation": {"paid_calls": "operator-standing-authorised",
                          "scope": "18 Q4T episodes, at most 54 Claude Code subscription calls, USD 72 local allocation",
                          "no_replay": True},
    }
    return {**value, "manifest_sha256": digest(value)}


def validate_manifest() -> tuple[dict, dict]:
    parent = frozen_parent()
    stage = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (stage != build_manifest(stage["date_utc"])
            or len(parent["rows"]) != 18
            or [row["sequence"] for row in parent["rows"]] != list(range(1, 19))
            or sum(row["episode_maximum_usd"] for row in parent["rows"]) != MAX_USD
            or any(row["ladder"] != [row["first_cell"], *screen.REPAIR_TAIL]
                   for row in parent["rows"])):
        raise LiveScreenError("Q4T S3 manifest or schedule differs")
    return parent, stage


def validate_approval(stage: dict) -> None:
    if APPROVAL.is_symlink():
        raise LiveScreenError("Q4T S3 approval is redirected")
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": stage["manifest_sha256"],
                "maximum_authorised_usd": MAX_USD,
                "maximum_provider_calls": MAX_CALLS,
                "credential_method": "claude-code-wsl-subscription"}
    if ({key: approval.get(key) for key in expected} != expected
            or set(approval) != set(expected) | {"approved_at_utc"}
            or not isinstance(approval.get("approved_at_utc"), str)
            or not approval["approved_at_utc"].strip()):
        raise LiveScreenError("Q4T S3 approval is not bound to the manifest")


def linux_root() -> str:
    process = subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
                              "wslpath", "-a", ROOT.as_posix()], capture_output=True,
                             text=True, timeout=30)
    if process.returncode or not process.stdout.strip().startswith("/mnt/"):
        raise LiveScreenError("repository is unavailable from WSL root")
    return process.stdout.strip()


def historical_and_runtime(parent: dict, stage: dict, linux: str) -> dict:
    command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "python3", "-B",
               f"{linux}/{SOURCE}", "--host-proof", "--repo", linux]
    process = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if process.returncode:
        raise LiveScreenError("Q4T historical or runtime host proof failed")
    proof = json.loads(process.stdout)
    if (proof.get("result") != "PASS" or proof.get("provider_calls") != 0
            or proof.get("provider_cost_usd") != 0
            or proof.get("parent_manifest_sha256") != parent["manifest_sha256"]
            or proof.get("stage_manifest_sha256") != stage["manifest_sha256"]
            or proof.get("proof_sha256") != digest({
                key: value for key, value in proof.items() if key != "proof_sha256"})):
        raise LiveScreenError("Q4T host proof is incomplete")
    return proof


def preflight(parent: dict, stage: dict, linux: str) -> dict:
    host = historical_and_runtime(parent, stage, linux)
    auth = canary.provider_free_probe(linux, "worker_wsl_q4t_auth_probe.py")
    probe = canary.provider_free_probe(linux, "worker_wsl_q4t_probe.py")
    proof = {"schema_version": 1, "result": "PASS",
             "parent_manifest_sha256": parent["manifest_sha256"],
             "stage_manifest_sha256": stage["manifest_sha256"],
             "source_sha256": {**parent["source_sha256"],
                               **stage["source_sha256"]},
             "historical_runtime": host, "auth": auth, "probe": probe}
    return {**proof, "evidence_sha256": digest(proof)}


def stop_campaign(reason: str, *, uncertain: bool) -> dict:
    path = RUN / "campaign.json"
    state = journal._read(path)
    if uncertain and state["rows"] and state["rows"][-1]["state"] == "provider-call-may-start":
        state["rows"][-1]["state"] = "uncertain"
    state.update(status="blocked", stop_reason=reason)
    journal._write(path, state)
    graded = [item["episode"] for item in state["rows"] if item["state"] == "graded"]
    by_family: dict[str, list[dict]] = {}
    for episode in graded:
        by_family.setdefault(episode["task_id"], []).append(episode)
    partial = {"schema_version": 1, "manifest_sha256": state["manifest_sha256"],
               "status": "incomplete", "stop_reason": reason,
               "settled_episodes": len(graded),
               "accounted_provider_calls": state["total_provider_calls"],
               "accounted_cost_usd": state["total_cost_usd"],
               "unresolved_intent": any(item["state"] == "uncertain"
                                        for item in state["rows"]),
               "complete_families": sum(len(arms) == 3 for arms in by_family.values()),
               "observations": [{
                   "task_id": item["task_id"],
                   "episode_label": item["episode_label"],
                   "executable_score": item["executable_grade"]["executable_score"],
                   "quality": item["quality_v2"]["quality"],
                   "hidden_accepted": item["quality_v2"]["hidden_accepted"],
                   "report_observability": item["quality_v2"]["report_observability"],
                   "charged_usd": item["settlement"]["charged_usd"],
               } for item in graded],
               "policy_decision": "retain-b0-incomplete-screen"}
    journal._write(RUN / "partial-analysis.json", partial)
    return journal._read(path)


def settle_campaign_episode(episode: dict, stop: str | None) -> dict:
    path = RUN / "campaign.json"
    state = journal._read(path)
    intent = state["rows"][-1]
    if (state["status"] != "running" or intent["state"] != "provider-call-may-start"
            or intent["sequence"] != episode["sequence"]
            or intent["task_id"] != episode["task_id"]
            or intent["episode_label"] != episode["episode_label"]):
        raise LiveScreenError("persisted intent differs from terminal receipt")
    intent.update(state="graded", episode=episode)
    state["total_cost_usd"] += episode["settlement"]["charged_usd"]
    state["total_provider_calls"] += episode["settlement"]["provider_calls"]
    if state["total_cost_usd"] > MAX_USD or state["total_provider_calls"] > MAX_CALLS:
        stop = "campaign allocation or call ceiling exceeded"
    if stop:
        state.update(status="blocked", stop_reason=stop)
    journal._write(path, state)
    return journal._read(path)


def adjudicate_episode(row: dict, episode: dict, parent: dict,
                       stage: dict) -> str | None:
    """Apply the frozen stop rule only to a fully validated episode."""
    evidence.validate_episode(row, episode, parent, stage)
    return settled_stop_reason(
        episode, episode_maximum_usd=row["episode_maximum_usd"],
        candidate_positive=(row["trigger"]["triggered"] is True
                            and row["episode_label"] == "sonnet-medium"))


def run_campaign() -> dict:
    if os.name != "nt":
        raise LiveScreenError("Q4T coordinator requires Windows")
    parent, stage = validate_manifest()
    validate_approval(stage)
    if stage["date_utc"] != dt.datetime.now(dt.timezone.utc).date().isoformat():
        raise LiveScreenError("Q4T S3 spend notice or manifest is not dated today UTC")
    if RUN.exists() or RUN.is_symlink():
        raise LiveScreenError("Q4T campaign already exists; no automatic replay")
    linux = linux_root()
    journal.start_campaign(RUN, stage["manifest_sha256"],
                           lambda: preflight(parent, stage, linux))
    for row in parent["rows"]:
        parent, stage = validate_manifest()
        validate_approval(stage)
        state = journal._read(RUN / "campaign.json")
        if (state["total_provider_calls"] >= MAX_CALLS
                or state["total_cost_usd"] >= MAX_USD):
            return stop_campaign("Q4T allocation exhausted", uncertain=False)
        if row["latin_position"] == 1:
            try:
                historical_and_runtime(parent, stage, linux)
            except (OSError, ValueError, TypeError, KeyError, RuntimeError,
                    subprocess.TimeoutExpired) as exc:
                return stop_campaign(
                    f"pre-dispatch host proof failed: {type(exc).__name__}",
                    uncertain=False)
        try:
            canary.provider_free_probe(linux, "worker_wsl_q4t_auth_probe.py")
        except (OSError, ValueError, TypeError, KeyError, RuntimeError,
                subprocess.TimeoutExpired) as exc:
            return stop_campaign(f"pre-dispatch Claude.ai auth probe failed: "
                                 f"{type(exc).__name__}", uncertain=False)
        journal.mark_intent(RUN, row["sequence"], row["task_id"],
                            row["episode_label"])
        command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "python3",
                   "-B", f"{linux}/{SOURCE}", "--episode", "--repo", linux,
                   "--sequence", str(row["sequence"])]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=7200)
            result = json.loads(process.stdout)
            if process.returncode or result.get("result") != "COMPLETE":
                raise LiveScreenError("WSL episode did not return a settled receipt")
            episode = result["episode"]
            stop = adjudicate_episode(row, episode, parent, stage)
            state = settle_campaign_episode(episode, stop)
        except (OSError, ValueError, TypeError, KeyError, RuntimeError,
                subprocess.TimeoutExpired) as exc:
            return stop_campaign(f"episode {row['sequence']} uncertain: "
                                 f"{type(exc).__name__}", uncertain=True)
        if state["status"] != "running":
            return stop_campaign(state["stop_reason"], uncertain=False)
    state = journal._read(RUN / "campaign.json")
    state.update(status="complete", completed_at_utc=dt.datetime.now(
        dt.timezone.utc).isoformat(timespec="seconds"))
    journal._write(RUN / "campaign.json", state)
    decision = analyse(journal._read(RUN / "campaign.json"), parent, stage)
    journal._write(RUN / "decision.json", decision)
    return journal._read(RUN / "campaign.json")


def run_episode(repo: Path, sequence: int) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0 or not 1 <= sequence <= 18:
        raise LiveScreenError("Q4T episode requires WSL root and a frozen sequence")
    parent, stage = validate_manifest()
    validate_approval(stage)
    if repo.resolve() != ROOT.resolve():
        raise LiveScreenError("Q4T episode repository differs from frozen root")
    if (sha(LAUNCHER) != stage["runtime_launcher_sha256"]
            or sha(SCHEMA) != stage["runtime_schema_sha256"]
            or sha(CLI) != stage["runtime_cli_sha256"]):
        raise LiveScreenError("Q4T runtime changed before the episode")
    row = parent["rows"][sequence - 1]
    state = journal._read(RUN / "campaign.json")
    if (state.get("status") != "running"
            or state.get("manifest_sha256") != stage["manifest_sha256"]
            or len(state.get("rows", [])) != sequence
            or state["rows"][-1] != {"sequence": sequence,
                                    "task_id": row["task_id"],
                                    "episode_label": row["episode_label"],
                                    "state": "provider-call-may-start"}):
        raise LiveScreenError("Q4T episode has no exact persisted provider intent")
    from task_executor import TaskExecutor
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q3_adapter import isolated_public_runner
    from worker_wsl_q4t_adapter import Q4TWslAdapter

    CredentialStore().inspect()
    task = build(row["task_id"])
    if (task["task_sha256"] != row["source_task_sha256"]
            or task["oracle_sha256"] != row["oracle_sha256"]
            or task["case_source_sha256"] != row["case_source_sha256"]
            or digest(screen.live_rubric(row))
               != parent["live_rubric_sha256"][row["task_id"]]):
        raise LiveScreenError("Q4T public task or rubric differs from frozen row")
    workspace = SEEDS / f"q4t-{stage['manifest_sha256'][:12]}-s3-{sequence:02d}"
    if workspace.exists() or workspace.is_symlink():
        raise LiveScreenError("Q4T actor workspace already exists; no replay")
    workspace.mkdir(mode=0o700)
    source = actor_root(row["task_id"])
    for name, expected in row["actor_files"].items():
        data = (source / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise LiveScreenError("Q4T actor source differs from frozen manifest")
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    protected = {name: value for name, value in row["actor_files"].items()
                 if name not in row["editable_paths"]}
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only declared existing source files may change"],
                "required_outputs": row["editable_paths"],
                "protected_paths": sorted(protected),
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = workspace / ".claude/q4t-acceptance.json"
    contract_path.parent.mkdir()
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    runner = isolated_public_runner(task)
    executor = TaskExecutor(workspace, Q4TWslAdapter(task), command_runner=runner)
    root_id = digest({"manifest": stage["manifest_sha256"],
                      "sequence": sequence})[:24]
    executor.admit(goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
                   scope=row["editable_paths"], permissions=["read", "edit"],
                   acceptance_path=contract_path, budget_usd=ALLOCATION,
                   authority_id=digest({"root": root_id, "authority": "q4t"})[:32],
                   actor="q4t-public", root_id=root_id,
                   task_id=f"{row['task_id'].lower()}-{row['episode_label']}",
                   input_paths=sorted(protected),
                   experimental_dispatch=dispatch(row, task, stage["manifest_sha256"]))
    outcome = executor.run(root_id)
    settled = journal.settle_stopped_patch(
        outcome, workspace, protected,
        lambda path, root_state, report: evidence.executable_grade(
            row, path, root_state, report, runner),
        lambda path: evidence.preserve(row, path, RUN))
    attempts = []
    for attempt in outcome["attempts"]:
        receipt = attempt.get("receipt") or {}
        if attempt.get("receipt_digest") != digest(receipt):
            raise LiveScreenError("persisted TaskExecutor receipt digest differs")
        boundary = receipt.get("command_contract", {}).get("q4t_boundary", {})
        attempts.append({"sequence": attempt["sequence"],
                         "invocation_id": attempt["invocation_id"],
                         "revision_id": attempt["revision_id"],
                         "receipt_digest": attempt["receipt_digest"],
                         "requested_cell": attempt["requested_cell"],
                         "requested_effort": receipt.get("requested_effort"),
                         "served_effort": receipt.get("served_effort"),
                         "status": receipt.get("status"),
                         "actual_model": receipt.get("actual_model"),
                         "root_models": receipt.get("root_models"),
                         "identity_valid": receipt.get("identity_valid"),
                         "terminal": receipt.get("terminal"),
                         "writer_stopped": receipt.get("writer_stopped"),
                         "cost_usd": receipt.get("cost_usd"),
                         "usage": receipt.get("usage"),
                         "wall_clock_s": receipt.get("wall_clock_s"),
                         "verification": (attempt.get("verification") or {}).get("status"),
                         "boundary": boundary,
                         "q4t_launcher_sha256": receipt.get(
                             "command_contract", {}).get("q4t_launcher_sha256"),
                         "evaluation_report": receipt.get("evaluation_report") or {},
                         "evaluation_report_digest": receipt.get("evaluation_report_digest"),
                         "evaluation_transport": receipt.get("evaluation_transport") or {},
                         "q4t_diagnostics": receipt.get("q4t_diagnostics") or {}})
    episode = {"sequence": sequence, "task_id": row["task_id"],
               "episode_label": row["episode_label"], "root_id": root_id,
               "root_state": outcome["state"], "budget": outcome["budget"],
               "attempts": attempts, "workspace": str(workspace),
               "parent_manifest_sha256": parent["manifest_sha256"],
               "stage_manifest_sha256": stage["manifest_sha256"],
               "protected_integrity": True, **settled}
    episode["evidence_sha256"] = digest(episode)
    evidence.validate_episode(row, episode, parent, stage, run_dir=RUN)
    (workspace / "q4t-s3-receipt.json").write_text(
        json.dumps(episode, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return episode


def dispatch(row: dict, task: dict, manifest_sha256: str) -> dict:
    assessment = worker_selector.assess({
        "task_kind": "implementation", "complexity": "complex",
        "verification": "executable", "context_tokens": 16000,
        "deadline_seconds": None, "failure_cause": "none",
        "prior_local_repairs": 0, "frame_confidence": "clear",
        "required_artefacts": task["editable_paths"],
        "evidence": [{"source": "operator", "reference": task["id"],
                      "claim": "repair the stated public issue"}],
    })
    return {"schema_version": 2, "arm": "alternative",
            "manifest_sha256": manifest_sha256,
            "assessment": assessment,
            "alternative_cell": row["first_cell"],
            "repair_cells": row["repair_cells"],
            "cost_ceiling_usd": row["episode_maximum_usd"]}


def _summary(rows: list[dict]) -> dict:
    return {"families": len(rows),
            "hidden_accepted": sum(bool(x["quality_v2"]["hidden_accepted"]) for x in rows),
            "mean_quality": sum(x["quality_v2"]["quality"] for x in rows) / len(rows),
            "critical_errors": sum(bool(x["quality_v2"]["critical_error"]) for x in rows),
            "unsupported_completions": sum(bool(x["quality_v2"]["unsupported_completion"])
                                           for x in rows),
            "invalid_reports": sum(x["quality_v2"]["report_observability"] != "present"
                                   for x in rows),
            "cost_usd": sum(x["settlement"]["charged_usd"] for x in rows),
            "provider_calls": sum(len(x["attempts"]) for x in rows)}


def analyse(state: dict, parent: dict, stage: dict) -> dict:
    if (state["status"] != "complete" or len(state["rows"]) != 18
            or any(item["state"] != "graded" for item in state["rows"])):
        raise LiveScreenError("Q4T analysis requires eighteen settled episodes")
    by_family = {}
    for item in state["rows"]:
        episode = item["episode"]
        by_family.setdefault(episode["task_id"], {})[episode["episode_label"]] = episode
    if (set(by_family) != set(FAMILIES)
            or any(set(arms) != set(screen.LABELS) for arms in by_family.values())):
        raise LiveScreenError("Q4T family arm inventory is incomplete")
    candidate, b0a, b0b, raw_medium, pairs = [], [], [], [], []
    for task_id in FAMILIES:
        arms = by_family[task_id]
        row = next(row for row in parent["rows"] if row["task_id"] == task_id)
        left, right, medium = (arms[label] for label in screen.LABELS)
        positive = row["trigger"]["triggered"]
        b0a.append(left)
        b0b.append(right)
        raw_medium.append(medium)
        candidate.append(medium if positive else left)
        lq, rq = left["quality_v2"], right["quality_v2"]
        flags = ("hidden_accepted", "critical_error", "unsupported_completion",
                 "report_observability")
        pairs.append({"task_id": task_id, "origin": row["origin"],
                      "flags_agree": all(lq[name] == rq[name] for name in flags),
                      "quality_difference": abs(lq["quality"] - rq["quality"]),
                      "trigger_positive": positive})
    upstream = [task_id != "T07" for task_id in FAMILIES]
    summaries = {"policy": _summary(candidate), "b0-a": _summary(b0a),
                 "b0-b": _summary(b0b), "all-medium-diagnostic": _summary(raw_medium),
                 "synthetic-t07": _summary([by_family["T07"]["sonnet-medium"]]),
                 "upstream-policy": _summary([item for item, keep in zip(candidate, upstream)
                                              if keep]),
                 "upstream-b0-a": _summary([item for item, keep in zip(b0a, upstream)
                                            if keep]),
                 "upstream-b0-b": _summary([item for item, keep in zip(b0b, upstream)
                                            if keep])}
    policy = summaries["policy"]
    comparisons = []
    for label in ("b0-a", "b0-b"):
        base = summaries[label]
        comparisons.append({"baseline": label,
                            "nonnegative_acceptance": policy["hidden_accepted"] >=
                                                       base["hidden_accepted"],
                            "nonnegative_quality": policy["mean_quality"] >=
                                                   base["mean_quality"],
                            "unsupported_not_above": policy["unsupported_completions"] <=
                                                     base["unsupported_completions"],
                            "invalid_reports_not_above": policy["invalid_reports"] <=
                                                         base["invalid_reports"],
                            "acceptance_gain": policy["hidden_accepted"] >
                                               base["hidden_accepted"],
                            "quality_gain_10": policy["mean_quality"] >=
                                               base["mean_quality"] + 10})
    mean_b0_cost = (summaries["b0-a"]["cost_usd"] +
                    summaries["b0-b"]["cost_usd"]) / 2
    upstream_policy = summaries["upstream-policy"]
    upstream_gain = all(
        upstream_policy["hidden_accepted"] > summaries[label]["hidden_accepted"]
        for label in ("upstream-b0-a", "upstream-b0-b")) or all(
        upstream_policy["mean_quality"] >= summaries[label]["mean_quality"] + 10
        for label in ("upstream-b0-a", "upstream-b0-b"))
    positives = sum(item["trigger_positive"] for item in pairs)
    guard = (policy["critical_errors"] == 0
             and upstream_gain
             and all(all(c[key] for key in ("nonnegative_acceptance",
                                          "nonnegative_quality",
                                          "unsupported_not_above",
                                          "invalid_reports_not_above"))
                     for c in comparisons)
             and (all(c["acceptance_gain"] for c in comparisons)
                  or all(c["quality_gain_10"] for c in comparisons))
             and policy["cost_usd"] <= 1.5 * mean_b0_cost
             and all(policy["cost_usd"] <= summaries[label]["cost_usd"] + positives
                     for label in ("b0-a", "b0-b")))
    value = {"schema_version": 1,
             "parent_manifest_sha256": parent["manifest_sha256"],
             "stage_manifest_sha256": stage["manifest_sha256"],
             "summaries": summaries, "comparisons": comparisons,
             "upstream_gain": upstream_gain,
             "b0_variability": pairs,
             "reserved_repetitions_if_later_freeze": 1 if all(
                 item["flags_agree"] and item["quality_difference"] < 10
                 for item in pairs) else 2,
             "policy_decision": "provisional-candidate" if guard else "retain-b0",
             "limits": ["Five upstream repositories plus one synthetic family.",
                        "No reserved-population inference or automatic promotion."]}
    return {**value, "decision_sha256": digest(value)}


def host_proof(repo: Path) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0 or repo.resolve() != ROOT.resolve():
        raise LiveScreenError("Q4T host proof requires WSL root and exact repo")
    parent, stage = validate_manifest()
    validate_approval(stage)
    s4 = journal._read(ROOT / "test/results/2026-09-26-worker-q4s-s4-run/campaign.json")
    c1 = journal._read(canary.RUN / "campaign.json")
    if (s4["state_sha256"] != parent["q4s_prior_campaign_state_sha256"]
            or s4["status"] != "blocked"
            or [(item["task_id"], item["episode_label"]) for item in s4["rows"]]
               != [("S03", label) for label in screen.LABELS]
            or c1["state_sha256"] != parent["c1_campaign_state_sha256"]
            or c1["status"] != "complete" or c1["total_provider_calls"] != 1
            or len(c1["rows"]) != 1 or c1["rows"][0]["state"] != "graded"
            or sha(LAUNCHER) != stage["runtime_launcher_sha256"]
            or sha(SCHEMA) != stage["runtime_schema_sha256"]
            or sha(CLI) != stage["runtime_cli_sha256"]):
        raise LiveScreenError("historical seal or Q4T runtime differs")
    value = {"schema_version": 1, "result": "PASS", "provider_calls": 0,
             "provider_cost_usd": 0,
             "parent_manifest_sha256": parent["manifest_sha256"],
             "stage_manifest_sha256": stage["manifest_sha256"],
             "s4_state_sha256": s4["state_sha256"],
             "c1_state_sha256": c1["state_sha256"],
             "cli_sha256": sha(CLI), "launcher_sha256": sha(LAUNCHER),
             "schema_sha256": sha(SCHEMA)}
    return {**value, "proof_sha256": digest(value)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--episode", action="store_true")
    parser.add_argument("--host-proof", action="store_true")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--sequence", type=int)
    args = parser.parse_args()
    if sum((args.prepare, args.check, args.run, args.episode, args.host_proof)) != 1:
        parser.error("choose exactly one action")
    try:
        if args.prepare:
            date = dt.datetime.now(dt.timezone.utc).date().isoformat()
            stage = build_manifest(date)
            if any(path.exists() or path.is_symlink() for path in (MANIFEST, APPROVAL)):
                raise LiveScreenError("refusing to overwrite Q4T S3 freeze")
            MANIFEST.write_text(json.dumps(stage, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
            approval = {"schema_version": 1, "decision": "approved",
                        "manifest_sha256": stage["manifest_sha256"],
                        "maximum_authorised_usd": MAX_USD,
                        "maximum_provider_calls": MAX_CALLS,
                        "credential_method": "claude-code-wsl-subscription",
                        "approved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(
                            timespec="seconds")}
            APPROVAL.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
            print(f"PASS: Q4T S3 manifest {stage['manifest_sha256']}")
        elif args.check:
            _, stage = validate_manifest()
            validate_approval(stage)
            print(f"PASS: Q4T S3 manifest {stage['manifest_sha256']}")
        elif args.run:
            state = run_campaign()
            print(f"Q4T S3 {state['status']}; {len(state['rows'])} episodes")
            return 0 if state["status"] == "complete" else 2
        elif args.host_proof:
            if args.repo is None:
                raise LiveScreenError("host proof repository is required")
            print(json.dumps(host_proof(args.repo), sort_keys=True))
        else:
            if args.repo is None or args.sequence is None:
                raise LiveScreenError("episode arguments are incomplete")
            episode = run_episode(args.repo, args.sequence)
            print(json.dumps({"result": "COMPLETE", "episode": episode},
                             sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        if args.episode or args.host_proof:
            print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        else:
            print(f"BLOCKED: Q4T S3: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
