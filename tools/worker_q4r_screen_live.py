#!/usr/bin/env python3
"""Run the exact Q4R public screen once with crash-safe episode checkpoints."""
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
import worker_q4r_screen as plan
import worker_selector
from worker_adapter import digest
from worker_quality_v2 import grade
from worker_q4r_structured import report_schema
from worker_q3_public_catalogue import FIXTURES, build, sha

RUN = plan.ROOT / "test/results/2026-09-25-worker-q4r-r1-run"


class LiveScreenError(RuntimeError):
    """A started Q4R episode cannot safely advance the campaign."""


def save(path: Path, value: dict) -> None:
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    value["state_sha256"] = digest(body)
    route._atomic_write_bytes(path, (json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def linux_root() -> str:
    process = subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root",
                              "--", "wslpath", "-a", plan.ROOT.as_posix()],
                             capture_output=True, text=True, timeout=30)
    if process.returncode or not process.stdout.strip().startswith("/mnt/"):
        raise LiveScreenError("repository is unavailable from WSL")
    return process.stdout.strip()


def assessment(task: dict) -> dict:
    return worker_selector.assess({
        "task_kind": "implementation", "complexity": "complex",
        "verification": "executable", "context_tokens": 12000,
        "deadline_seconds": None, "failure_cause": "none",
        "prior_local_repairs": 0, "frame_confidence": "clear",
        "required_artefacts": task["editable_paths"],
        "evidence": [{"source": "operator", "reference": task["id"],
                      "claim": "repair the stated public issue"}],
    })


def dispatch(row: dict, task: dict, manifest_sha256: str) -> dict:
    return {"schema_version": 2, "arm": "alternative",
            "manifest_sha256": manifest_sha256,
            "assessment": assessment(task),
            "alternative_cell": row["first_cell"],
            "repair_cells": row["repair_cells"],
            "cost_ceiling_usd": row["episode_maximum_usd"]}


def live_grade(task_id: str, rubric: dict, workspace: Path, root_state: str,
               report_record: dict) -> tuple[dict, dict]:
    """Combine isolated executable evidence with the bound final report."""
    from worker_wsl_q3_public import grade_candidate

    executable = grade_candidate(task_id, workspace, root_state)
    case_results = {row["milestone"]: row["passed"]
                    for row in executable["cases"]}
    calibration_record = json.loads(plan.CALIBRATION.read_text(encoding="utf-8"))
    calibrated = next(row for row in calibration_record["rows"]
                      if row["task_id"] == task_id)
    baseline = {row["milestone"]: row["passed"]
                for row in calibrated["source_grades"]["baseline"]["cases"]}
    parsed = report_record.get("report")
    present = report_record.get("observability") == "present" and isinstance(parsed, dict)
    executable_passes = [case_results[row["id"]] for row in rubric["predicates"]
                         if row["category"] in {"behaviour", "invariant"}]
    improved = any(not baseline[name] and passed
                   for name, passed in case_results.items())
    report_aligned = bool(present and (
        (all(executable_passes) and parsed["status"] == "completed"
         and not parsed["remaining"])
        or (not all(executable_passes) and parsed["status"] in {"partial", "blocked"}
            and bool(parsed["remaining"]))))
    observations = {}
    for row in rubric["predicates"]:
        if row["id"] == "diagnosis":
            passed = bool(present and improved and parsed["evidence"])
        elif row["id"] == "report":
            passed = report_aligned
        else:
            passed = case_results[row["id"]]
        observations[row["id"]] = {
            "passed": passed,
            "evidence": f"root Q4R observation for {task_id}: {row['id']} "
                        f"{'passed' if passed else 'failed'}"}
    expected = report_record["binding"]
    quality = grade(rubric, observations, report_record, root_state=root_state,
                    execution_checks={"python3 -B public_check.py":
                                      executable["public_pass"]},
                    expected_binding=expected)
    return executable, quality


def preserve(row: dict, workspace: Path) -> dict:
    target = RUN / "patches" / f"{row['sequence']:02d}-{row['task_id'].lower()}-{row['episode_label']}"
    if target.exists():
        raise LiveScreenError("candidate snapshot already exists")
    hashes = {}
    for relative in row["editable_paths"]:
        source = workspace / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        hashes[relative] = sha(destination)
    record = {"schema_version": 1, "sequence": row["sequence"],
              "task_id": row["task_id"], "episode_label": row["episode_label"],
              "files": hashes}
    record["snapshot_sha256"] = digest(record)
    (target / "snapshot.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def validate_receipt(row: dict, receipt: dict) -> None:
    attempts = receipt.get("attempts")
    budget = receipt.get("budget") or {}
    quality = receipt.get("quality_v2") or {}
    executable = receipt.get("executable_grade") or {}
    if (receipt.get("task_id") != row["task_id"]
            or receipt.get("episode_label") != row["episode_label"]
            or receipt.get("root_state") not in {"accepted", "partial", "failed"}
            or budget.get("unresolved") or not isinstance(attempts, list)
            or not 1 <= len(attempts) <= 3
            or type(budget.get("spent_usd")) not in (int, float)
            or not math.isfinite(budget["spent_usd"])
            or not 0 <= budget["spent_usd"] <= row["episode_maximum_usd"]
            or not math.isclose(sum(item.get("cost_usd", float("nan"))
                                    for item in attempts), budget["spent_usd"],
                                abs_tol=1e-8)
            or quality.get("task_sha256") != row["task_sha256"]
            or quality.get("grade_sha256") != digest({
                key: value for key, value in quality.items() if key != "grade_sha256"})
            or quality.get("inconclusive")
            or executable.get("task_sha256") != row["source_task_sha256"]
            or executable.get("oracle_sha256") != row["oracle_sha256"]
            or executable.get("case_source_sha256") != row["case_source_sha256"]
            or not executable.get("oracle_read_denied")
            or not executable.get("source_workspace_unchanged")
            or executable.get("provider_calls") != 0
            or receipt.get("protected_sha256") != {name: value for name, value in
                row["actor_files"].items() if name not in row["editable_paths"]}
            or (receipt.get("snapshot") or {}).get("snapshot_sha256") != digest({
                key: value for key, value in receipt["snapshot"].items()
                if key != "snapshot_sha256"})):
        raise LiveScreenError("episode receipt, grade, snapshot or budget is invalid")
    for index, attempt in enumerate(attempts):
        cell = row["ladder"][index]
        report = attempt.get("evaluation_report") or {}
        transport = attempt.get("evaluation_transport") or {}
        if (not attempt.get("terminal") or not attempt.get("writer_stopped")
                or not attempt.get("identity_valid")
                or attempt.get("requested_cell") != cell
                or attempt.get("actual_model") != model_registry.resolve_cell(cell)[
                    "cli_model"]
                or attempt.get("requested_effort") != model_registry.resolve_cell(cell)[
                    "effort"]
                or type(attempt.get("cost_usd")) not in (int, float)
                or not math.isfinite(attempt["cost_usd"])
                or attempt["cost_usd"] < 0
                or not attempt.get("q1_record_sha256")
                or not attempt.get("q1_spec_sha256")
                or attempt.get("evaluation_report_digest") != digest(report)
                or transport.get("mode") != "claude-code-json-schema-v1"
                or transport.get("schema_sha256") != digest(report_schema())
                or transport.get("structured_output_present") is not True
                or report.get("binding", {}).get("requested_cell") != cell):
            raise LiveScreenError("attempt identity, report, isolation or cost is invalid")


def analyse(state: dict, manifest: dict) -> dict:
    grouped = {label: [] for label in plan.LABELS}
    for item in state["rows"]:
        if item.get("state") != "graded":
            raise LiveScreenError("analysis requires every episode")
        grouped[item["episode"]["episode_label"]].append(item["episode"])
    summaries = {}
    for label, episodes in grouped.items():
        summaries[label] = {
            "episodes": len(episodes),
            "accepted": sum(bool(row["quality_v2"]["hidden_accepted"])
                            for row in episodes),
            "mean_quality": sum(row["quality_v2"]["quality"]
                                for row in episodes) / len(episodes),
            "critical_errors": sum(bool(row["quality_v2"]["critical_error"])
                                   for row in episodes),
            "unsupported_completions": sum(bool(
                row["quality_v2"]["unsupported_completion"]) for row in episodes),
            "cost_usd": sum(row["budget"]["spent_usd"] for row in episodes),
            "provider_calls": sum(len(row["attempts"]) for row in episodes),
        }
    b0_labels = ("b0-a", "b0-b")
    mean_b0_cost = sum(summaries[name]["cost_usd"] for name in b0_labels) / 2
    candidate_rows = []
    for label in ("sonnet-high",):
        current = summaries[label]
        comparisons = []
        for baseline in b0_labels:
            base = summaries[baseline]
            comparisons.append({
                "baseline": baseline,
                "non_negative_acceptance": current["accepted"] >= base["accepted"],
                "non_negative_quality": current["mean_quality"] >= base["mean_quality"],
                "acceptance_gain": current["accepted"] > base["accepted"],
                "quality_gain_10": current["mean_quality"] >= base["mean_quality"] + 10,
                "unsupported_not_above": current["unsupported_completions"]
                                         <= base["unsupported_completions"],
            })
        qualifies = (current["critical_errors"] == 0
                     and all(row["unsupported_not_above"] for row in comparisons)
                     and all(row["non_negative_acceptance"]
                             and row["non_negative_quality"] for row in comparisons)
                     and all(row["acceptance_gain"] or row["quality_gain_10"]
                             for row in comparisons)
                     and current["cost_usd"] <= 1.5 * mean_b0_cost
                     and current["cost_usd"] <= mean_b0_cost + len(plan.TASKS))
        candidate_rows.append({"episode_label": label, "summary": current,
                               "comparisons": comparisons, "qualifies": qualifies,
                               "dominated": False})
    for row in candidate_rows:
        for other in candidate_rows:
            if row is other or not row["qualifies"] or not other["qualifies"]:
                continue
            a, b = row["summary"], other["summary"]
            if (b["cost_usd"] <= a["cost_usd"]
                    and b["mean_quality"] >= a["mean_quality"]
                    and (b["cost_usd"] < a["cost_usd"]
                         or b["mean_quality"] > a["mean_quality"])):
                row["dominated"] = True
    eligible = [row for row in candidate_rows
                if row["qualifies"] and not row["dominated"]]
    eligible.sort(key=lambda row: (row["summary"]["cost_usd"],
                                   -row["summary"]["mean_quality"]))
    pairs = []
    by_label_task = {(row["episode_label"], row["task_id"]): row
                     for item in state["rows"] for row in [item["episode"]]}
    for task_id in plan.TASKS:
        left, right = (by_label_task[(label, task_id)] for label in b0_labels)
        lq, rq = left["quality_v2"], right["quality_v2"]
        flags = ("hidden_accepted", "critical_error", "unsupported_completion",
                 "report_observability")
        agrees = all(lq[name] == rq[name] for name in flags)
        pairs.append({"task_id": task_id, "flags_agree": agrees,
                      "quality_difference": abs(lq["quality"] - rq["quality"])})
    repetitions = 1 if all(row["flags_agree"]
                           and row["quality_difference"] < 10 for row in pairs) else 2
    value = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "summaries": summaries, "candidates": candidate_rows,
             "selected_candidate": eligible[0]["episode_label"] if eligible else None,
             "policy_decision": "provisional-candidate" if eligible else "retain-b0",
             "b0_variability": pairs,
             "reserved_repetitions_if_q4r_freezes": repetitions,
             "limits": ["Four public families are development evidence only.",
                        "No reserved-population inference is made."]}
    return {**value, "decision_sha256": digest(value)}


def run_campaign() -> dict:
    manifest = json.loads(plan.MANIFEST.read_text(encoding="utf-8"))
    plan.validate(manifest, check_host=True)
    approval = json.loads(plan.APPROVAL.read_text(encoding="utf-8"))
    plan.validate_approval(manifest, approval)
    if RUN.exists():
        raise LiveScreenError("Q4R run already exists; no automatic replay")
    RUN.mkdir(mode=0o700)
    state = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "status": "running", "created_at_utc":
                 dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "rows": [], "next_sequence": 1, "total_cost_usd": 0.0,
             "total_provider_calls": 0}
    save(RUN / "campaign.json", state)
    linux = linux_root()
    for row in manifest["rows"]:
        plan.validate(manifest, check_host=True)
        plan.validate_approval(manifest, approval)
        if (state["total_cost_usd"] >= plan.MAXIMUM_USD
                or state["total_provider_calls"] >= plan.MAX_TASK_CALLS):
            state.update(status="blocked", stop_reason="task allocation exhausted")
            save(RUN / "campaign.json", state)
            return state
        item = {"sequence": row["sequence"], "task_id": row["task_id"],
                "episode_label": row["episode_label"],
                "state": "provider-call-may-start"}
        state["rows"].append(item)
        save(RUN / "campaign.json", state)
        command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
                   "python3", "-B", f"{linux}/tools/worker_q4r_screen_live.py",
                   "--episode", "--repo", linux, "--sequence", str(row["sequence"]),
                   "--manifest", f"{linux}/{plan.MANIFEST.relative_to(plan.ROOT).as_posix()}",
                   "--approval", f"{linux}/{plan.APPROVAL.relative_to(plan.ROOT).as_posix()}"]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=7200)
            result = json.loads(process.stdout.strip())
            if process.returncode or result.get("result") != "COMPLETE":
                raise LiveScreenError(result.get("error_type", "episode incomplete"))
            receipt = result["episode"]
            validate_receipt(row, receipt)
        except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired,
                LiveScreenError) as exc:
            item.update(state="uncertain", failure_type=type(exc).__name__)
            state.update(status="blocked", stop_reason="uncertain episode")
            save(RUN / "campaign.json", state)
            return state
        item.update(state="graded", episode=receipt)
        state["total_cost_usd"] += receipt["budget"]["spent_usd"]
        state["total_provider_calls"] += len(receipt["attempts"])
        state["next_sequence"] = row["sequence"] + 1
        save(RUN / "campaign.json", state)
    state["status"] = "complete"
    state["completed_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(
        timespec="seconds")
    save(RUN / "campaign.json", state)
    decision = analyse(state, manifest)
    save(RUN / "decision.json", decision)
    return state


def run_episode(repo: Path, sequence: int, manifest_path: Path,
                approval_path: Path) -> dict:
    if os.geteuid() != 0:
        raise LiveScreenError("episode requires WSL root")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    plan.validate_approval(manifest, approval)
    if manifest.get("manifest_sha256") != digest({
            key: value for key, value in manifest.items() if key != "manifest_sha256"}):
        raise LiveScreenError("Q4R manifest digest is invalid")
    if (any(sha(repo / name) != expected
            for name, expected in manifest["source_sha256"].items())
            or sha(repo / plan.TRIGGERS.relative_to(plan.ROOT))
               != manifest["public_trigger_sha256"]
            or sha(repo / plan.NOTICE.relative_to(plan.ROOT))
               != manifest["spend_notice_sha256"]
            or sha(repo / plan.HOST.relative_to(plan.ROOT))
               != manifest["host_sha256"]):
        raise LiveScreenError("Q4R source, trigger, notice or host evidence changed")
    row = next(item for item in manifest["rows"] if item["sequence"] == sequence)
    task = build(row["task_id"])
    _, rubric = plan.q4.live_rubric(row["task_id"])
    if (task["task_sha256"] != row["source_task_sha256"]
            or rubric != row["rubric"] or rubric["task_sha256"] != row["task_sha256"]
            or row["ladder"] != [row["first_cell"], *plan.REPAIR_TAIL]
            or row["episode_maximum_usd"] != plan.ALLOCATION):
        raise LiveScreenError("public task differs from approved Q4R row")

    from task_executor import TaskExecutor
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q3_adapter import isolated_public_runner
    from worker_wsl_q4r_adapter import LAUNCHER, RUNTIME, Q4RWslAdapter

    if (sha(LAUNCHER) != manifest["runtime_launcher_sha256"]
            or sha(RUNTIME / "q4r-report-schema.json")
               != manifest["runtime_schema_sha256"]):
        raise LiveScreenError("Q4R installed launcher or schema changed")

    CredentialStore().inspect()
    name = f"q4r-{manifest['manifest_sha256'][:12]}-{sequence:02d}"
    workspace = SEEDS / name
    if workspace.exists() or workspace.is_symlink():
        raise LiveScreenError("Q4R task workspace already exists; no replay")
    workspace.mkdir(mode=0o700)
    source = repo / "test/fixtures/worker_q3_public" / row["task_id"] / "actor"
    for relative, expected in row["actor_files"].items():
        target = workspace / relative
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        data = (source / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise LiveScreenError("public source differs from Q4R manifest")
        target.write_bytes(data)
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only declared existing source files may change"],
                "required_outputs": row["editable_paths"],
                "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = workspace / ".claude/q4r-acceptance.json"
    contract_path.parent.mkdir()
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    executor = TaskExecutor(workspace, Q4RWslAdapter(task),
                            command_runner=isolated_public_runner(task))
    root_id = digest({"manifest": manifest["manifest_sha256"],
                      "sequence": sequence})[:24]
    executor.admit(goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
                   scope=row["editable_paths"], permissions=["read", "edit"],
                   acceptance_path=contract_path, budget_usd=plan.ALLOCATION,
                   authority_id=digest({"root": root_id, "authority": "q4r"})[:32],
                   actor="q4r-public", root_id=root_id,
                   task_id=f"{row['task_id'].lower()}-{row['episode_label']}",
                   input_paths=protected,
                   experimental_dispatch=dispatch(row, task,
                                                  manifest["manifest_sha256"]))
    outcome = executor.run(root_id)
    if outcome["state"] not in {"accepted", "partial", "failed"}:
        raise LiveScreenError("root outcome needs manual reconciliation")
    attempts = []
    for attempt in outcome["attempts"]:
        receipt = attempt.get("receipt") or {}
        boundary = receipt.get("command_contract", {}).get("q4r_boundary", {})
        report = receipt.get("evaluation_report") or {}
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
                         "changed_paths": boundary.get("changed_paths"),
                         "evaluation_report": report,
                         "evaluation_report_digest": receipt.get(
                             "evaluation_report_digest"),
                         "evaluation_transport": receipt.get("evaluation_transport")})
    if not attempts:
        raise LiveScreenError("terminal episode has no worker attempt")
    executable, quality = live_grade(row["task_id"], rubric, workspace,
                                     outcome["state"], attempts[-1][
                                         "evaluation_report"])
    snapshot = preserve(row, workspace)
    return {"task_id": row["task_id"], "episode_label": row["episode_label"],
            "root_id": root_id, "root_state": outcome["state"],
            "budget": outcome["budget"], "attempts": attempts,
            "executable_grade": executable, "quality_v2": quality,
            "snapshot": snapshot, "workspace": str(workspace),
            "protected_sha256": {name: sha(workspace / name)
                                 for name in protected}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--episode", action="store_true")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--sequence", type=int)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args()
    try:
        if args.episode:
            if not all((args.repo, args.sequence, args.manifest, args.approval)):
                raise LiveScreenError("episode arguments are incomplete")
            result = run_episode(args.repo, args.sequence, args.manifest,
                                 args.approval)
            print(json.dumps({"result": "COMPLETE", "episode": result},
                             sort_keys=True))
        elif args.run:
            state = run_campaign()
            print(f"Q4R {state['status']}; {len(state['rows'])} episode rows")
            return 0 if state["status"] == "complete" else 2
        else:
            parser.error("choose --run or --episode")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired, StopIteration) as exc:
        if args.episode:
            print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        else:
            print(f"BLOCKED: Q4R: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
