#!/usr/bin/env python3
"""Grade and validate stopped Q4T screen episodes before applying stop policy.

The actor never receives the oracle. File verification runs under WSL root
after the worker has stopped; the coordinator independently checks the sealed
projection before it makes a campaign decision.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

import model_registry
from worker_adapter import digest
from worker_q4r_structured import report_schema
from worker_q4s_public_grade import run as run_oracle
from worker_q4t_public import ROOT, actor_root, build, oracle_root, sha
from worker_q4t_screen import live_rubric
from worker_quality_v2 import grade, parse_report


class EvidenceError(RuntimeError):
    """A stopped episode lacks independently checkable evidence."""


def executable_grade(row: dict, workspace: Path, root_state: str,
                     report_record: dict, public_runner) -> tuple[dict, dict]:
    """Grade executable cases in an evaluator copy and leave the actor intact."""
    task = build(row["task_id"])
    oracle_dir = oracle_root(row["task_id"])
    oracle = json.loads((oracle_dir / task["oracle_file"]).read_text(encoding="utf-8"))
    before = {name: sha(workspace / name) for name in row["actor_files"]}
    public = public_runner(["python3", "-B", "public_check.py"], cwd=workspace,
                           capture_output=True, timeout=30, shell=False)
    with tempfile.TemporaryDirectory(prefix="q4t-evaluator-") as temporary:
        actor = Path(temporary)
        for name in row["actor_files"]:
            destination = actor / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(workspace / name, destination)
        cases = []
        for case in oracle["cases"]:
            process = run_oracle(
                [sys.executable, "-B", str(oracle_dir / task["case_file"])],
                actor, stdin=json.dumps(case["input"]))
            try:
                passed = (process.returncode == 0
                          and json.loads(process.stdout) == case["expected"])
            except (ValueError, TypeError):
                passed = False
            cases.append({"milestone": case["milestone"], "passed": passed,
                          "weight": case["weight"], "exit_code": process.returncode})
    if before != {name: sha(workspace / name) for name in row["actor_files"]}:
        raise EvidenceError("evaluator changed the stopped actor workspace")
    result = {"task_sha256": task["task_sha256"],
              "oracle_sha256": task["oracle_sha256"],
              "case_source_sha256": task["case_source_sha256"],
              "public_pass": public.returncode == 0,
              "public_isolated": hasattr(public, "isolation_evidence"),
              "source_workspace_unchanged": True,
              "cases": cases,
              "executable_score": sum(case["weight"] for case in cases
                                      if case["passed"])}
    result["evaluator_sha256"] = digest(result)
    baseline = _baseline(row["task_id"])
    case_passed = {case["milestone"]: case["passed"] for case in cases}
    report = report_record.get("report")
    present = report_record.get("observability") == "present" and isinstance(report, dict)
    all_executable = all(case_passed.values()) and result["public_pass"]
    report_aligned = bool(present and (
        (all_executable and report["status"] == "completed" and not report["remaining"])
        or (not all_executable and report["status"] in {"partial", "blocked"}
            and bool(report["remaining"]))))
    improved = any(not baseline[name] and passed for name, passed in case_passed.items())
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
        observations[name] = {"passed": passed,
                              "evidence": f"Q4T {row['task_id']} evaluator case {name}: "
                              f"{'passed' if passed else 'failed'}"}
    quality = grade(rubric, observations, report_record,
                    root_state=root_state if root_state != "blocked" else "failed",
                    execution_checks={"python3 -B public_check.py": result["public_pass"]},
                    expected_binding=report_record["binding"])
    return result, quality


def _baseline(task_id: str) -> dict[str, bool]:
    path = (ROOT / "test/results/2026-09-26-worker-q4s-public-calibration.json"
            if task_id != "T07" else
            ROOT / "test/results/2026-09-26-worker-q4t-public-calibration.json")
    evidence = json.loads(path.read_text(encoding="utf-8"))
    row = (next(row for row in evidence["rows"] if row["task_id"] == task_id)
           if task_id != "T07" else evidence)
    return {case["milestone"]: case["passed"] for case in row["grades"][0]["cases"]}


def preserve(row: dict, workspace: Path, run_dir: Path) -> dict:
    """Create one immutable patch snapshot before returning an episode."""
    target = run_dir / "patches" / (f"{row['sequence']:02d}-"
                                    f"{row['task_id'].lower()}-{row['episode_label']}")
    if target.exists() or target.is_symlink():
        raise EvidenceError("episode patch snapshot already exists")
    files = {}
    for name in row["editable_paths"]:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(workspace / name, destination)
        files[name] = sha(destination)
    value = {"schema_version": 1, "sequence": row["sequence"],
             "task_id": row["task_id"], "episode_label": row["episode_label"],
             "files": files}
    value["snapshot_sha256"] = digest(value)
    (target / "snapshot.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def validate_episode(row: dict, episode: dict, parent: dict, stage: dict,
                     *, run_dir: Path | None = None) -> None:
    """Check identity, receipt, ledger, grade and snapshot before policy use.

    With ``run_dir`` this also re-hashes the stopped actor and copied patch.
    The Windows coordinator repeats all serialised checks on the returned
    projection; file checks ran inside the WSL root child.
    """
    if not isinstance(episode, dict):
        raise EvidenceError("episode is not a mapping")
    body = {key: value for key, value in episode.items() if key != "evidence_sha256"}
    if episode.get("evidence_sha256") != digest(body):
        raise EvidenceError("episode evidence digest differs")
    if (episode.get("sequence") != row["sequence"]
            or episode.get("task_id") != row["task_id"]
            or episode.get("episode_label") != row["episode_label"]
            or episode.get("parent_manifest_sha256") != parent["manifest_sha256"]
            or episode.get("stage_manifest_sha256") != stage["manifest_sha256"]
            or episode.get("root_state") not in {"accepted", "partial", "failed", "blocked"}
            or episode.get("protected_integrity") is not True):
        raise EvidenceError("episode identity or protected integrity differs")
    protected = {name: value for name, value in row["actor_files"].items()
                 if name not in row["editable_paths"]}
    if episode.get("protected_sha256") != protected:
        raise EvidenceError("protected source hash inventory differs")
    attempts = episode.get("attempts") or []
    budget = episode.get("budget") or {}
    settlement = episode.get("settlement") or {}
    amount = settlement.get("charged_usd")
    if (not isinstance(attempts, list) or not 1 <= len(attempts) <= 3
            or budget.get("unresolved")
            or settlement.get("cost_settled") is not True
            or settlement.get("writer_stopped") is not True
            or settlement.get("provider_calls") != len(attempts)
            or type(amount) not in (int, float) or not math.isfinite(amount)
            or amount < 0 or type(budget.get("spent_usd")) not in (int, float)
            or not math.isclose(amount, budget["spent_usd"], abs_tol=1e-8)):
        raise EvidenceError("episode charge or writer is unsettled")
    ledger = budget.get("invocations") or {}
    if not isinstance(ledger, dict) or set(ledger) != {
            item.get("invocation_id") for item in attempts}:
        raise EvidenceError("attempts do not match the budget ledger")
    for index, attempt in enumerate(attempts):
        cell = row["ladder"][index]
        resolved = model_registry.resolve_cell(cell)
        invocation = attempt.get("invocation_id")
        charge = attempt.get("cost_usd")
        account = ledger.get(invocation) or {}
        report = attempt.get("evaluation_report") or {}
        transport = attempt.get("evaluation_transport") or {}
        diagnostics = attempt.get("q4t_diagnostics") or {}
        boundary = attempt.get("boundary") or {}
        binding = report.get("binding") or {}
        if (attempt.get("requested_cell") != cell
                or attempt.get("requested_effort") != resolved["effort"]
                or attempt.get("actual_model") != resolved["cli_model"]
                or diagnostics.get("real_root_models") != [resolved["cli_model"]]
                or attempt.get("identity_valid") is not True
                or attempt.get("terminal") is not True
                or attempt.get("writer_stopped") is not True
                or type(charge) not in (int, float) or not math.isfinite(charge)
                or charge < 0 or account.get("state") != "settled"
                or type(account.get("cost_usd")) not in (int, float)
                or not math.isclose(charge, account["cost_usd"], abs_tol=1e-8)
                or attempt.get("evaluation_report_digest") != digest(report)
                or transport.get("mode") != parent["transport_mode"]
                or transport.get("schema_sha256") != parent["report_schema_sha256"]
                or transport.get("structured_retry_limit") != parent["structured_retry_limit"]
                or transport.get("schema_sha256") != digest(report_schema())
                or attempt.get("q4t_launcher_sha256") != stage["runtime_launcher_sha256"]
                or diagnostics.get("invalid_line_count") != 0
                or not isinstance(boundary.get("q1_record_sha256"), str)
                or len(boundary["q1_record_sha256"]) != 64
                or not isinstance(boundary.get("q1_spec_sha256"), str)
                or len(boundary["q1_spec_sha256"]) != 64
                or not isinstance(boundary.get("changed_paths"), list)
                or not set(boundary["changed_paths"]).issubset(row["editable_paths"])
                or binding.get("invocation_id") != invocation
                or binding.get("revision_id") != attempt.get("revision_id")
                or binding.get("requested_cell") != cell
                or binding.get("task_sha256") != live_rubric(row)["task_sha256"]
                or binding.get("final_revision_sha256")
                   != digest(boundary.get("after_sha256"))):
            raise EvidenceError("attempt receipt, model, report or ledger differs")
        if report.get("observability") == "present":
            raw = report.get("raw_utf8")
            if (not isinstance(raw, str)
                    or hashlib.sha256(raw.encode("utf-8")).hexdigest()
                       != report.get("raw_sha256")
                    or parse_report(raw) != report.get("report")
                    or transport.get("structured_output_present") is not True):
                raise EvidenceError("present structured report bytes differ")
        elif (report.get("observability") != "transport-invalid"
              or any(report.get(key) is not None for key in
                     ("raw_utf8", "raw_sha256", "report"))
              or transport.get("structured_output_present") is not False):
            raise EvidenceError("absent report is not a bounded transport failure")
    if not math.isclose(sum(item["cost_usd"] for item in attempts), amount,
                        abs_tol=1e-8):
        raise EvidenceError("attempt charges differ from episode settlement")
    executable = episode.get("executable_grade") or {}
    quality = episode.get("quality_v2") or {}
    snapshot = episode.get("snapshot") or {}
    oracle_dir = oracle_root(row["task_id"])
    task = build(row["task_id"])
    oracle = json.loads((oracle_dir / task["oracle_file"]).read_text(encoding="utf-8"))
    expected_cases = [(case["milestone"], case["weight"]) for case in oracle["cases"]]
    actual_cases = [(case.get("milestone"), case.get("weight"))
                    for case in executable.get("cases") or []]
    if (executable.get("evaluator_sha256") != digest({
            key: value for key, value in executable.items()
            if key != "evaluator_sha256"})
            or executable.get("task_sha256") != row["source_task_sha256"]
            or executable.get("oracle_sha256") != row["oracle_sha256"]
            or executable.get("case_source_sha256") != row["case_source_sha256"]
            or executable.get("public_isolated") is not True
            or executable.get("source_workspace_unchanged") is not True
            or actual_cases != expected_cases
            or executable.get("executable_score") != sum(
                case["weight"] for case in executable["cases"]
                if case.get("passed") is True)
            or quality.get("grade_sha256") != digest({
                key: value for key, value in quality.items() if key != "grade_sha256"})
            or quality.get("task_sha256") != live_rubric(row)["task_sha256"]
            or quality.get("report_observability")
               != attempts[-1]["evaluation_report"]["observability"]
            or quality.get("inconclusive") is not (
                quality.get("report_observability") == "transport-invalid")
            or any(quality.get("predicate_results", {}).get(case["milestone"])
                   is not case.get("passed") for case in executable["cases"])
            or snapshot.get("snapshot_sha256") != digest({
                key: value for key, value in snapshot.items()
                if key != "snapshot_sha256"})
            or snapshot.get("sequence") != row["sequence"]
            or snapshot.get("task_id") != row["task_id"]
            or snapshot.get("episode_label") != row["episode_label"]
            or set(snapshot.get("files") or {}) != set(row["editable_paths"])):
        raise EvidenceError("evaluator grade, quality or snapshot digest differs")
    eligible = (episode["root_state"] != "blocked" and all(
        attempt["status"] == "completed"
        and attempt["identity_valid"] is True
        and attempt["evaluation_report"]["observability"] == "present"
        for attempt in attempts))
    if episode.get("qualification_eligible") is not eligible:
        raise EvidenceError("qualification flag differs from stopped attempts")
    if quality.get("report_observability") != "present" and (
            quality.get("hidden_accepted") is not False
            or quality.get("component_scores", {}).get("diagnosis") != 0
            or quality.get("component_scores", {}).get("report") != 0):
        raise EvidenceError("invalid report earned acceptance or report credit")
    if run_dir is not None:
        workspace = Path(episode["workspace"])
        target = run_dir / "patches" / (f"{row['sequence']:02d}-"
                                        f"{row['task_id'].lower()}-{row['episode_label']}")
        if workspace.is_symlink() or target.is_symlink():
            raise EvidenceError("workspace or snapshot path is redirected")
        for name, expected in protected.items():
            path = workspace / name
            if path.is_symlink() or sha(path) != expected:
                raise EvidenceError("protected file differs after grading")
        for name, expected in snapshot["files"].items():
            path = target / name
            if path.is_symlink() or sha(path) != expected or sha(workspace / name) != expected:
                raise EvidenceError("snapshot bytes differ from stopped actor")
        saved = json.loads((target / "snapshot.json").read_text(encoding="utf-8"))
        if saved != snapshot:
            raise EvidenceError("saved snapshot record differs")
