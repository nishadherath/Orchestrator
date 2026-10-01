#!/usr/bin/env python3
"""Run the frozen Q4S six-family screen with durable episode intents.

The S2 manifest fixes tasks, trigger, arm order and stop rules. This S4 child
manifest additionally binds the paid driver and dated S4 notice. Every WSL
episode gets a fresh actor and a TaskExecutor root; a started episode is never
automatically replayed after a crash or ambiguous receipt.
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
import tempfile
from pathlib import Path

import model_registry
import route
import worker_q4s_admission as journal
import worker_q4s_canary_live as canary
import worker_q4s_screen as screen
import worker_selector
from worker_adapter import digest
from worker_adapter import WorkerRequest
from worker_q4s_public_catalogue import ORACLES, build
from worker_q4s_public_grade import run as run_oracle
from worker_q4s_public_source import FIXTURES, SOURCES as FAMILIES
from worker_quality_v2 import grade, validate_rubric
from worker_q4r_structured import report_schema


ROOT = screen.ROOT
SOURCE = "tools/worker_q4s_screen_live.py"
NOTICE = ROOT / "docs/stage-results/worker-q4s-s4-spend-notice-2026-09-26.md"
MANIFEST = ROOT / "test/results/2026-09-26-worker-q4s-s4-manifest.json"
APPROVAL = ROOT / "test/results/2026-09-26-worker-q4s-s4-approval.json"
RUN = ROOT / "test/results/2026-09-26-worker-q4s-s4-run"
ALLOCATION = 4.0
MAX_CALLS = 54
MAX_USD = 72.0


class ScreenError(RuntimeError):
    """The S4 screen cannot safely start or advance."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parent_and_canary() -> tuple[dict, dict]:
    parent = canary.frozen_parent()
    _, stage3 = canary.validate_manifest()
    canary.validate_approval(stage3)
    state = journal._read(canary.RUN / "campaign.json")
    if (state.get("status") != "complete"
            or state.get("manifest_sha256") != stage3["manifest_sha256"]
            or len(state.get("rows", [])) != 2
            or state.get("total_provider_calls") != 2
            or type(state.get("total_cost_usd")) not in (int, float)
            or state["total_cost_usd"] > 6.0
            or any(row.get("state") != "graded" for row in state["rows"])):
        raise ScreenError("S3 canary is not sealed and complete")
    return parent, state


def live_rubric(row: dict) -> dict:
    """Bind the frozen predicate weights to TaskExecutor's report identity."""
    value = dict(row["rubric"])
    issue = (FIXTURES / row["task_id"] / "actor/ISSUE.md").read_text(
        encoding="utf-8")
    value["task_sha256"] = digest({"issue": issue,
                                   "allowed_edits": tuple(row["editable_paths"])})
    return validate_rubric(value)


def build_manifest(date_utc: str) -> dict:
    dt.date.fromisoformat(date_utc)
    parent, canary_state = parent_and_canary()
    if NOTICE.is_symlink() or not NOTICE.is_file():
        raise ScreenError("dated S4 spend notice is missing or redirected")
    live = {row["task_id"]: digest(live_rubric(row)) for row in parent["rows"]}
    value = {
        "schema_version": 1, "profile": "worker-q4s-s4-six-family-screen",
        "date_utc": date_utc,
        "parent_manifest_sha256": parent["manifest_sha256"],
        "s3_manifest_sha256": canary_state["manifest_sha256"],
        "s3_campaign_sha256": sha(canary.RUN / "campaign.json"),
        "s3_state_sha256": canary_state["state_sha256"],
        "spend_notice_sha256": sha(NOTICE),
        "source_sha256": {SOURCE: sha(ROOT / SOURCE)},
        "parent_rows_sha256": digest(parent["rows"]),
        "live_rubric_sha256": live,
        "episode_count": 18, "family_count": 6,
        "episode_allocation_usd": ALLOCATION,
        "maximum_allocation_usd": MAX_USD,
        "maximum_provider_calls": MAX_CALLS,
        "policy_counterfactual": parent["policy_counterfactual"],
        "selection_rules": parent["selection_rules"],
        "stop_rules": parent["stop_rules"],
        "authorisation": parent["authorisation"],
    }
    return {**value, "manifest_sha256": digest(value)}


def validate_manifest() -> tuple[dict, dict]:
    parent, _ = parent_and_canary()
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if value != build_manifest(value["date_utc"]):
        raise ScreenError("S4 child manifest differs from frozen inputs")
    if (len(parent["rows"]) != 18 or len(FAMILIES) != 6
            or [row["sequence"] for row in parent["rows"]]
               != list(range(1, 19))
            or sum(row["episode_maximum_usd"] for row in parent["rows"])
               != MAX_USD
            or any(row["ladder"] != [row["first_cell"], *screen.REPAIR_TAIL]
                   for row in parent["rows"])):
        raise ScreenError("S4 schedule or budget differs")
    return parent, value


def validate_approval(manifest: dict) -> None:
    if APPROVAL.is_symlink():
        raise ScreenError("S4 approval is redirected")
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_authorised_usd": MAX_USD,
                "maximum_provider_calls": MAX_CALLS,
                "credential_method": "claude-code-wsl-subscription"}
    if ({key: approval.get(key) for key in expected} != expected
            or set(approval) != set(expected) | {"approved_at_utc"}
            or not isinstance(approval.get("approved_at_utc"), str)
            or not approval["approved_at_utc"].strip()):
        raise ScreenError("S4 approval is not bound to the exact manifest")


def linux_root() -> str:
    process = subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root",
                              "--", "wslpath", "-a", ROOT.as_posix()],
                             capture_output=True, text=True, timeout=30)
    if process.returncode or not process.stdout.strip().startswith("/mnt/"):
        raise ScreenError("repository is unavailable from WSL root")
    return process.stdout.strip()


def assessment(task: dict) -> dict:
    return worker_selector.assess({
        "task_kind": "implementation", "complexity": "complex",
        "verification": "executable", "context_tokens": 16000,
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


def executable_grade(row: dict, workspace: Path, root_state: str,
                     report_record: dict) -> tuple[dict, dict]:
    """Grade a stopped actor against protected cases in an evaluator copy."""
    from worker_wsl_q3_adapter import isolated_public_runner

    task_id = row["task_id"]
    task = build(task_id)
    oracle = json.loads((ORACLES / task["oracle_file"]).read_text(encoding="utf-8"))
    before = {name: sha(workspace / name) for name in row["actor_files"]}
    public = isolated_public_runner(task)(
        ["python3", "-B", "public_check.py"], cwd=workspace,
        capture_output=True, timeout=30, shell=False)
    with tempfile.TemporaryDirectory(prefix="q4s-s4-grade-") as raw:
        actor = Path(raw)
        for relative in row["actor_files"]:
            destination = actor / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(workspace / relative, destination)
        cases = []
        for case in oracle["cases"]:
            process = run_oracle(
                [sys.executable, "-B", str(ORACLES / task["case_file"])],
                actor, stdin=json.dumps(case["input"]))
            try:
                passed = (process.returncode == 0
                          and json.loads(process.stdout) == case["expected"])
            except (ValueError, TypeError):
                passed = False
            cases.append({"milestone": case["milestone"], "passed": passed,
                          "weight": case["weight"],
                          "exit_code": process.returncode})
    unchanged = before == {name: sha(workspace / name)
                           for name in row["actor_files"]}
    if not unchanged:
        raise ScreenError("evaluator altered the source workspace")
    result = {"task_sha256": task["task_sha256"],
              "oracle_sha256": task["oracle_sha256"],
              "case_source_sha256": task["case_source_sha256"],
              "public_pass": public.returncode == 0,
              "public_isolated": hasattr(public, "isolation_evidence"),
              "source_workspace_unchanged": unchanged,
              "oracle_absent_from_actor": task["oracle_file"] not in row["actor_files"],
              "cases": cases,
              "executable_score": sum(case["weight"] for case in cases
                                      if case["passed"])}
    calibration = json.loads(screen.CALIBRATION.read_text(encoding="utf-8"))
    baseline_row = next(item for item in calibration["rows"]
                        if item["task_id"] == task_id)
    baseline = {case["milestone"]: case["passed"] for case in
                baseline_row["grades"][0]["cases"]}
    case_passed = {case["milestone"]: case["passed"] for case in cases}
    report = report_record.get("report")
    present = report_record.get("observability") == "present" and isinstance(report, dict)
    all_executable = all(case_passed.values()) and result["public_pass"]
    report_aligned = bool(present and (
        (all_executable and report["status"] == "completed" and not report["remaining"])
        or (not all_executable and report["status"] in {"partial", "blocked"}
            and bool(report["remaining"]))))
    improved = any(not baseline[name] and passed
                   for name, passed in case_passed.items())
    rubric = live_rubric(row)
    observations = {}
    for predicate in rubric["predicates"]:
        name = predicate["id"]
        if name == "diagnosis":
            passed = bool(present and improved and report["evidence"])
        elif name == "report":
            passed = report_aligned
        else:
            passed = case_passed[name]
        observations[name] = {
            "passed": passed,
            "evidence": f"Q4S {task_id} evaluator case {name}: "
                        f"{'passed' if passed else 'failed'}"}
    quality = grade(
        rubric, observations, report_record,
        root_state=root_state if root_state in {"accepted", "partial", "failed"}
                   else "failed",
        execution_checks={"python3 -B public_check.py": result["public_pass"]},
        expected_binding=report_record["binding"])
    return result, quality


def preserve(row: dict, workspace: Path) -> dict:
    target = RUN / "patches" / (f"{row['sequence']:02d}-"
                                f"{row['task_id'].lower()}-{row['episode_label']}")
    if target.exists() or target.is_symlink():
        raise ScreenError("episode patch snapshot already exists")
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


def validate_receipt(row: dict, episode: dict, parent: dict,
                     stage: dict) -> str | None:
    """Validate settled evidence; return a settled campaign-stop reason if any."""
    budget = episode.get("budget") or {}
    attempts = episode.get("attempts") or []
    settlement = episode.get("settlement") or {}
    amount = settlement.get("charged_usd")
    quality = episode.get("quality_v2") or {}
    executable = episode.get("executable_grade") or {}
    if (episode.get("task_id") != row["task_id"]
            or episode.get("episode_label") != row["episode_label"]
            or episode.get("sequence") != row["sequence"]
            or episode.get("parent_manifest_sha256") != parent["manifest_sha256"]
            or episode.get("stage_manifest_sha256") != stage["manifest_sha256"]
            or episode.get("root_state") not in {"accepted", "partial", "failed", "blocked"}
            or budget.get("unresolved")
            or not isinstance(attempts, list) or not 1 <= len(attempts) <= 3
            or settlement.get("provider_calls") != len(attempts)
            or settlement.get("cost_settled") is not True
            or settlement.get("writer_stopped") is not True
            or type(amount) not in (int, float) or not math.isfinite(amount)
            or amount < 0
            or type(budget.get("spent_usd")) not in (int, float)
            or not math.isclose(amount, budget["spent_usd"], abs_tol=1e-8)
            or quality.get("task_sha256") != live_rubric(row)["task_sha256"]
            or quality.get("grade_sha256") != digest({
                key: value for key, value in quality.items() if key != "grade_sha256"})
            or executable.get("task_sha256") != row["source_task_sha256"]
            or executable.get("oracle_sha256") != row["oracle_sha256"]
            or executable.get("case_source_sha256") != row["case_source_sha256"]
            or executable.get("source_workspace_unchanged") is not True
            or executable.get("public_isolated") is not True
            or episode.get("protected_sha256") != {
                name: value for name, value in row["actor_files"].items()
                if name not in row["editable_paths"]}
            or (episode.get("snapshot") or {}).get("snapshot_sha256")
               != digest({key: value for key, value in episode["snapshot"].items()
                          if key != "snapshot_sha256"})):
        raise ScreenError("S4 terminal evidence, source grade or charge is invalid")
    stop = ("settled episode allocation overrun"
            if amount > row["episode_maximum_usd"] else None)
    if quality.get("inconclusive") is True:
        stop = "settled invalid structured transport"
    for index, attempt in enumerate(attempts):
        expected_cell = row["ladder"][index]
        resolved = model_registry.resolve_cell(expected_cell)
        report = attempt.get("evaluation_report") or {}
        transport = attempt.get("evaluation_transport") or {}
        if (attempt.get("requested_cell") != expected_cell
                or attempt.get("terminal") is not True
                or attempt.get("writer_stopped") is not True
                or type(attempt.get("cost_usd")) not in (int, float)
                or not math.isfinite(attempt["cost_usd"])
                or attempt["cost_usd"] < 0
                or attempt.get("evaluation_report_digest") != digest(report)
                or not isinstance(attempt.get("q1_record_sha256"), str)
                or len(attempt["q1_record_sha256"]) != 64
                or not isinstance(attempt.get("q1_spec_sha256"), str)
                or len(attempt["q1_spec_sha256"]) != 64
                or not isinstance(attempt.get("changed_paths"), list)
                or not set(attempt["changed_paths"]).issubset(row["editable_paths"])):
            raise ScreenError("S4 attempt has uncertain charge or isolation evidence")
        if (attempt.get("identity_valid") is not True
                or attempt.get("actual_model") != resolved["cli_model"]
                or attempt.get("requested_effort") != resolved["effort"]):
            stop = "settled model identity mismatch"
        if (transport.get("mode") != "claude-code-json-schema-v1"
                or transport.get("schema_sha256") != digest(report_schema())):
            stop = "settled invalid structured transport"
    if not math.isclose(sum(item["cost_usd"] for item in attempts), amount,
                        abs_tol=1e-8):
        raise ScreenError("S4 attempt charges differ from settled episode")
    if episode["root_state"] == "blocked":
        stop = "settled blocked root requires review"
    return stop


def stop_campaign(reason: str, *, uncertain: bool) -> dict:
    path = RUN / "campaign.json"
    state = journal._read(path)
    if uncertain and state["rows"][-1]["state"] == "provider-call-may-start":
        state["rows"][-1]["state"] = "uncertain"
    state.update(status="blocked", stop_reason=reason)
    journal._write(path, state)
    return journal._read(path)


def settle_campaign_episode(episode: dict, stop: str | None) -> dict:
    path = RUN / "campaign.json"
    state = journal._read(path)
    intent = state["rows"][-1]
    if (state["status"] != "running"
            or intent["state"] != "provider-call-may-start"
            or intent["sequence"] != episode["sequence"]
            or intent["task_id"] != episode["task_id"]
            or intent["episode_label"] != episode["episode_label"]):
        raise ScreenError("S4 persisted intent differs from terminal receipt")
    intent.update(state="graded", episode=episode)
    state["total_cost_usd"] += episode["settlement"]["charged_usd"]
    state["total_provider_calls"] += episode["settlement"]["provider_calls"]
    if state["total_cost_usd"] > MAX_USD or state["total_provider_calls"] > MAX_CALLS:
        stop = "campaign allocation or call ceiling exceeded"
    if stop:
        state.update(status="blocked", stop_reason=stop)
    journal._write(path, state)
    return journal._read(path)


def preflight(parent: dict, stage: dict, linux: str) -> dict:
    auth = canary.provider_free_probe(linux, "worker_wsl_q4s_auth_probe.py")
    probe = canary.provider_free_probe(linux, "worker_wsl_q4s_probe.py")
    proof = {"schema_version": 1, "result": "PASS",
             "parent_manifest_sha256": parent["manifest_sha256"],
             "stage_manifest_sha256": stage["manifest_sha256"],
             "source_sha256": {**parent["source_sha256"],
                               **stage["source_sha256"]},
             "auth": auth, "probe": probe}
    return {**proof, "evidence_sha256": digest(proof)}


def summary(rows: list[dict]) -> dict:
    return {"families": len(rows),
            "hidden_accepted": sum(bool(x["quality_v2"]["hidden_accepted"]) for x in rows),
            "mean_quality": sum(x["quality_v2"]["quality"] for x in rows) / len(rows),
            "critical_errors": sum(bool(x["quality_v2"]["critical_error"]) for x in rows),
            "unsupported_completions": sum(bool(x["quality_v2"]["unsupported_completion"])
                                           for x in rows),
            "invalid_reports": sum(x["quality_v2"]["report_observability"] != "present"
                                   for x in rows),
            "cost_usd": sum(x["budget"]["spent_usd"] for x in rows),
            "provider_calls": sum(len(x["attempts"]) for x in rows)}


def analyse(state: dict, parent: dict, stage: dict) -> dict:
    """Apply frozen policy to independent families, retaining diagnostic arms."""
    if (state["status"] != "complete" or len(state["rows"]) != 18
            or any(item["state"] != "graded" for item in state["rows"])):
        raise ScreenError("analysis requires all eighteen settled episodes")
    by_family = {}
    for item in state["rows"]:
        episode = item["episode"]
        by_family.setdefault(episode["task_id"], {})[episode["episode_label"]] = episode
    if (set(by_family) != set(FAMILIES)
            or any(set(arms) != set(screen.LABELS) for arms in by_family.values())):
        raise ScreenError("S4 analysis arm inventory is incomplete")
    candidate, b0a, b0b, raw_medium = [], [], [], []
    pairs = []
    for task_id, arms in by_family.items():
        row = next(row for row in parent["rows"] if row["task_id"] == task_id)
        positive = row["trigger"]["triggered"]
        left, right, medium = (arms[label] for label in screen.LABELS)
        b0a.append(left)
        b0b.append(right)
        raw_medium.append(medium)
        candidate.append(medium if positive else left)
        lq, rq = left["quality_v2"], right["quality_v2"]
        flags = ("hidden_accepted", "critical_error", "unsupported_completion",
                 "report_observability")
        pairs.append({"task_id": task_id,
                      "flags_agree": all(lq[name] == rq[name] for name in flags),
                      "quality_difference": abs(lq["quality"] - rq["quality"]),
                      "trigger_positive": positive})
    summaries = {"policy": summary(candidate), "b0-a": summary(b0a),
                 "b0-b": summary(b0b), "all-medium-diagnostic": summary(raw_medium)}
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
    positives = sum(item["trigger_positive"] for item in pairs)
    guard = (policy["critical_errors"] == 0
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
             "b0_variability": pairs,
             "reserved_repetitions_if_q4r_freezes": 1 if all(
                 x["flags_agree"] and x["quality_difference"] < 10 for x in pairs) else 2,
             "policy_decision": "provisional-candidate" if guard else "retain-b0",
             "limits": ["Six public families are development evidence only.",
                        "No reserved-population inference or automatic promotion."]}
    return {**value, "decision_sha256": digest(value)}


def run_campaign() -> dict:
    if os.name != "nt":
        raise ScreenError("S4 coordinator requires Windows; WSL is for --episode")
    parent, stage = validate_manifest()
    validate_approval(stage)
    if stage["date_utc"] != dt.datetime.now(dt.timezone.utc).date().isoformat():
        raise ScreenError("S4 spend notice or manifest is not dated today UTC")
    if RUN.exists() or RUN.is_symlink():
        raise ScreenError("S4 campaign already exists; no automatic replay")
    linux = linux_root()
    journal.start_campaign(RUN, stage["manifest_sha256"],
                           lambda: preflight(parent, stage, linux))
    for row in parent["rows"]:
        parent, stage = validate_manifest()
        validate_approval(stage)
        state = journal._read(RUN / "campaign.json")
        if (state["total_provider_calls"] >= MAX_CALLS
                or state["total_cost_usd"] >= MAX_USD):
            return stop_campaign("S4 allocation exhausted", uncertain=False)
        journal.mark_intent(RUN, row["sequence"], row["task_id"],
                            row["episode_label"])
        command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
                   "python3", "-B", f"{linux}/{SOURCE}", "--episode",
                   "--repo", linux, "--sequence", str(row["sequence"])]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=7200)
            result = json.loads(process.stdout)
            if process.returncode or result.get("result") != "COMPLETE":
                raise ScreenError("WSL episode did not return a settled receipt")
            episode = result["episode"]
            stop = validate_receipt(row, episode, parent, stage)
            state = settle_campaign_episode(episode, stop)
        except (OSError, ValueError, TypeError, KeyError, ScreenError,
                journal.Q4SAdmissionError, subprocess.TimeoutExpired) as exc:
            return stop_campaign(f"episode {row['sequence']} uncertain: "
                                 f"{type(exc).__name__}", uncertain=True)
        if state["status"] != "running":
            return state
        if row["latin_position"] == 3:
            family = [item["episode"] for item in state["rows"][-3:]]
            if row["trigger"]["triggered"] and next(
                    item for item in family if item["episode_label"] == "sonnet-medium"
                    )["quality_v2"]["critical_error"]:
                return stop_campaign("positive candidate critical error after complete family",
                                     uncertain=False)
    state = journal._read(RUN / "campaign.json")
    state.update(status="complete", completed_at_utc=dt.datetime.now(
        dt.timezone.utc).isoformat(timespec="seconds"))
    journal._write(RUN / "campaign.json", state)
    decision = analyse(state, parent, stage)
    journal._write(RUN / "decision.json", decision)
    return journal._read(RUN / "campaign.json")


def run_episode(repo: Path, sequence: int) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0 or not 1 <= sequence <= 18:
        raise ScreenError("S4 episode requires WSL root and a frozen sequence")
    parent, stage = validate_manifest()
    validate_approval(stage)
    if repo.resolve() != ROOT.resolve():
        raise ScreenError("S4 episode repository differs from frozen root")
    row = parent["rows"][sequence - 1]
    state = journal._read(RUN / "campaign.json")
    if (state.get("status") != "running"
            or state.get("manifest_sha256") != stage["manifest_sha256"]
            or len(state.get("rows", [])) != sequence
            or state["rows"][-1] != {"sequence": sequence,
                                    "task_id": row["task_id"],
                                    "episode_label": row["episode_label"],
                                    "state": "provider-call-may-start"}):
        raise ScreenError("S4 episode has no exact persisted provider-call intent")
    from task_executor import TaskExecutor
    from worker_wsl_auth import CredentialStore
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q3_adapter import isolated_public_runner
    from worker_wsl_q4s_adapter import Q4SWslAdapter

    CredentialStore().inspect()
    task = build(row["task_id"])
    if (task["task_sha256"] != row["source_task_sha256"]
            or task["oracle_sha256"] != row["oracle_sha256"]
            or task["case_source_sha256"] != row["case_source_sha256"]
            or digest(live_rubric(row)) != stage["live_rubric_sha256"][row["task_id"]]):
        raise ScreenError("S4 source task or rubric differs from frozen row")
    workspace = SEEDS / f"q4s-{stage['manifest_sha256'][:12]}-s4-{sequence:02d}"
    if workspace.exists() or workspace.is_symlink():
        raise ScreenError("S4 actor workspace already exists; no replay")
    workspace.mkdir(mode=0o700)
    source = repo / "test/fixtures/worker_q4s_public" / row["task_id"] / "actor"
    for relative, expected in row["actor_files"].items():
        data = (source / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ScreenError("S4 actor source differs from frozen manifest")
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    protected = {key: value for key, value in row["actor_files"].items()
                 if key not in row["editable_paths"]}
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only declared existing source files may change"],
                "required_outputs": row["editable_paths"],
                "protected_paths": sorted(protected),
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = workspace / ".claude/q4s-acceptance.json"
    contract_path.parent.mkdir()
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    executor = TaskExecutor(workspace, Q4SWslAdapter(task),
                            command_runner=isolated_public_runner(task))
    root_id = digest({"manifest": stage["manifest_sha256"],
                      "sequence": sequence})[:24]
    executor.admit(goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
                   scope=row["editable_paths"], permissions=["read", "edit"],
                   acceptance_path=contract_path, budget_usd=ALLOCATION,
                   authority_id=digest({"root": root_id, "authority": "q4s"})[:32],
                   actor="q4s-public", root_id=root_id,
                   task_id=f"{row['task_id'].lower()}-{row['episode_label']}",
                   input_paths=sorted(protected),
                   experimental_dispatch=dispatch(row, task,
                                                  stage["manifest_sha256"]))
    outcome = executor.run(root_id)
    settled = journal.settle_stopped_patch(
        outcome, workspace, protected,
        lambda path, root_state, report: executable_grade(row, path, root_state, report),
        lambda path: preserve(row, path))
    attempts = []
    for attempt in outcome["attempts"]:
        receipt = attempt.get("receipt") or {}
        boundary = receipt.get("command_contract", {}).get("q4s_boundary", {})
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
                         "evaluation_report": receipt.get("evaluation_report") or {},
                         "evaluation_report_digest": receipt.get(
                             "evaluation_report_digest"),
                         "evaluation_transport": receipt.get("evaluation_transport")})
    episode = {"sequence": sequence, "task_id": row["task_id"],
               "episode_label": row["episode_label"], "root_id": root_id,
               "root_state": outcome["state"], "budget": outcome["budget"],
               "attempts": attempts, "workspace": str(workspace),
               "parent_manifest_sha256": parent["manifest_sha256"],
               "stage_manifest_sha256": stage["manifest_sha256"], **settled}
    evidence = {**episode, "evidence_sha256": digest(episode)}
    (workspace / "q4s-s4-receipt.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
            if MANIFEST.exists() or MANIFEST.is_symlink():
                raise ScreenError("S4 manifest already exists")
            value = build_manifest(dt.datetime.now(dt.timezone.utc).date().isoformat())
            MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
            print(f"PASS: S4 manifest {value['manifest_sha256']}")
        elif args.check:
            _, value = validate_manifest()
            print(f"PASS: S4 manifest {value['manifest_sha256']}")
        elif args.run:
            state = run_campaign()
            print(f"Q4S S4 {state['status']}; {len(state['rows'])} episodes")
            return 0 if state["status"] == "complete" else 2
        else:
            if args.repo is None or args.sequence is None:
                raise ScreenError("S4 episode arguments are incomplete")
            episode = run_episode(args.repo, args.sequence)
            print(json.dumps({"result": "COMPLETE", "episode": episode},
                             sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired, StopIteration) as exc:
        if args.episode:
            print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        else:
            print(f"BLOCKED: Q4S S4: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
