#!/usr/bin/env python3
"""Single-use H03 development pilot; prepare is provider-free.

Paid modes remain closed until their exact manifest-bound notice is approved.
The actor, public risk check and protected oracle have separate inventories.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from zoneinfo import ZoneInfo

import controller_campaign_manifest
import controller_dispatch
import controller_evaluation
import controller_workflow
import controller_x5_h03_risk
import controller_x5_v6_screen as screen
import controller_x5_v7_pilot as v7
import controller_x5_public_risk_review as review
import dispatch_budget
import task_executor
from controller_wsl_interpreter import WslPublicInterpreter
from controller_x5_recovery_isolation import hidden_evaluation_tree
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import GRAFT, MCP, NODE
from worker_wsl_q4u_adapter import Q4UWslAdapter, isolated_public_runner


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "test" / "fixtures" / "controller_x5_h03"
SOURCE = FIXTURE / "actor"
CATALOGUE = FIXTURE / "catalogue.json"
RISK_MANIFEST = FIXTURE / "risk-manifest.json"
MANIFEST_PATH = ROOT / "test/results/2026-10-01-controller-x5-h03b-pilot-manifest.json"
RUN_DIR = ROOT / "test/results/2026-10-01-controller-x5-h03b-pilot-run"
NOTICE_PATH = ROOT / "test/results/2026-10-01-controller-x5-h03b-pilot-cost-notice.json"
EDITABLE = "tools/system_controller.py"
LIMITS = {"B0": 5.0, "S": 5.0, "A": 6.0}
TOTAL_LIMIT = 16.0
ASSESSMENT_LIMIT = 0.5
SCOPE = "H03 authored Controller defect: one producer and conditional public-risk S/A review"
PRODUCER_PROMPT = "Investigate the reported Controller gap, run the public check and report truthful progress."
REVIEW_PROMPT = "Check the documented critique re-entry risk, run the public recheck and report truthful progress."


class PilotStop(RuntimeError):
    """A frozen, isolation, accounting or single-use boundary is not proved."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise PilotStop(f"missing or redirected record: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def case() -> dict:
    catalogue = load(CATALOGUE)
    risk = load(RISK_MANIFEST)
    catalogue_body = {key: value for key, value in catalogue.items() if key != "catalogue_sha256"}
    if (sha(json.dumps(catalogue_body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")) != catalogue.get("catalogue_sha256")
            or risk != controller_x5_h03_risk.expected()
            or risk.get("source_catalogue_sha256") != catalogue["catalogue_sha256"]
            or catalogue.get("editable_paths") != [EDITABLE]
            or len(catalogue.get("actor_files", {})) != catalogue.get("actor_file_count")):
        raise PilotStop("H03 public catalogue or risk decision changed")
    for name, expected in catalogue["actor_files"].items():
        path = SOURCE / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise PilotStop(f"H03 public actor changed: {name}")
    if sha((FIXTURE / "oracle.py").read_bytes()) != catalogue["private_sha256"]["oracle.py"]:
        raise PilotStop("H03 private oracle changed")
    return {"id": "H03", "actor_files": catalogue["actor_files"],
            "editable_paths": [EDITABLE], "public_command": ["python3", "-B", "public_check.py"],
            "risk": risk["risk"], "risk_digest": risk["risk_digest"],
            "catalogue_sha256": catalogue["catalogue_sha256"],
            "risk_manifest_sha256": risk["risk_manifest_sha256"],
            "oracle_sha256": catalogue["private_sha256"]["oracle.py"],
            "risk_check_sha256": risk["risk_check_sha256"]}


def freeze() -> dict:
    row = case()
    body = {"schema_version": 1, "stage": "x5-h03-authored-development",
            "case_id": "H03", "origin": "retrospective local Controller integration failure",
            "actor_files": row["actor_files"], "editable_paths": row["editable_paths"],
            "catalogue_sha256": row["catalogue_sha256"],
            "risk_manifest_sha256": row["risk_manifest_sha256"],
            "oracle_sha256": row["oracle_sha256"],
            "risk_check_sha256": row["risk_check_sha256"],
            "schedule": ["B0", "public-risk-check-if-accepted", "S-if-risk-fails", "A-if-S-settled",
                         "protected-grade-after-both"],
            "root_limits_usd": LIMITS, "maximum_authorised_usd": TOTAL_LIMIT,
            "assessment_allowance_usd": ASSESSMENT_LIMIT,
            "worker_policy": "one Sonnet-low Q4U producer; one Sonnet-low review call per eligible arm",
            "controller_profile": "standard", "controller_invocations_per_A": 1,
            "eligibility": "settled identity-valid public success followed by a qualified public risk failure",
            "stop_rule": "stop on public risk success, uncertainty, source drift, replay or invalid identity",
            "analysis_rule": "A minus S protected quality and critical error, with cost and elapsed time",
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "host": controller_campaign_manifest.host_record(),
            "credential_method": "claude-code-wsl-subscription"}
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def manifest() -> dict:
    saved = load(MANIFEST_PATH)
    if saved != freeze():
        raise PilotStop("H03 manifest or runtime package changed")
    return saved


def actor_path(row: dict, arm: str) -> Path:
    if arm not in {"B0", "S", "A"}:
        raise PilotStop("unknown H03 arm")
    return SEEDS / f"x5-h03-{row['manifest_sha256'][:16]}-{arm.lower()}"


def root_id(row: dict, arm: str) -> str:
    return controller_evaluation.digest(
        {"manifest": row["manifest_sha256"], "case": "H03", "arm": arm})[:24]


def task(row: dict, arm: str) -> dict:
    if arm == "B0":
        files = row["actor_files"]
    else:
        inputs = load(RUN_DIR / "pair/inputs.json")
        if inputs.get("manifest_sha256") != row["manifest_sha256"]:
            raise PilotStop("H03 successor inventory belongs to another manifest")
        files = inputs["actor_files"]
    return {"id": "H03", "actor_files": files, "editable_paths": [EDITABLE],
            "public_command": ["python3", "-B", "public_check.py"]}


def entry(row: dict, arm: str) -> task_executor.TaskExecutor:
    contract = task(row, arm)
    return task_executor.TaskExecutor(
        actor_path(row, arm), Q4UWslAdapter(contract),
        command_runner=isolated_public_runner(contract),
        campaign_prompt=PRODUCER_PROMPT if arm == "B0" else REVIEW_PROMPT)


def verify_actor(row: dict, arm: str) -> None:
    actor = actor_path(row, arm)
    for name, expected in task(row, arm)["actor_files"].items():
        path = actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise PilotStop(f"H03 public source changed before {arm} dispatch: {name}")


def copy_actor(row: dict, arm: str, files: dict[str, bytes]) -> None:
    actor = actor_path(row, arm)
    if actor.exists() or actor.is_symlink() or actor.resolve().parent != SEEDS.resolve():
        raise PilotStop("H03 single-use actor path already exists or escaped seeds")
    actor.mkdir(mode=0o700)
    for name, data in files.items():
        if name not in row["actor_files"] and name not in {
                "acceptance.json", "REVIEW.md", "RISK-REPORT.json", "risk_check.py"}:
            raise PilotStop(f"unexpected H03 public file: {name}")
        path = actor / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def admit(row: dict, arm: str) -> None:
    actor = actor_path(row, arm)
    files = task(row, arm)["actor_files"]
    protected = sorted(set(files) - {EDITABLE})
    criteria = ["The isolated public check passes"] if arm == "B0" else [
        "The isolated public check continues to pass",
        "The recorded critique re-entry risk is checked and its outcome reported truthfully",
        "The caller's external acceptance criteria remain unchanged in committed frames",
    ]
    contract = {"version": 1, "kind": "command", "criteria": criteria,
                "constraints": [f"Only {EDITABLE} may change"],
                "required_outputs": [EDITABLE], "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = actor / ".claude/h03-acceptance.json"
    contract_path.parent.mkdir(exist_ok=True)
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    rid = root_id(row, arm)
    goal = actor / ("ISSUE.md" if arm == "B0" else "REVIEW.md")
    entry(row, arm).admit(
        goal=goal.read_text(encoding="utf-8"), scope=[EDITABLE],
        permissions=["read", "edit"], input_paths=protected,
        acceptance_path=contract_path, budget_usd=LIMITS[arm],
        authority_id=controller_evaluation.digest(
            {"root": rid, "grant": "x5-h03-development"})[:32],
        actor="x5-h03-authored-development", root_id=rid,
        task_id=f"h03-{arm.lower()}")


def controller_host(actor: Path) -> None:
    config = actor / ".mcp.json"
    config.write_bytes(MCP.read_bytes())
    config.chmod(0o600)
    graph = subprocess.run([str(NODE), str(GRAFT), "build", str(actor)], cwd=actor,
                           capture_output=True, text=True, timeout=120, check=False)
    if graph.returncode or not (actor / "graft").is_dir():
        raise PilotStop("H03 Controller Graft build failed: " + graph.stderr[-300:])
    controller_dispatch.ControllerRuntimeAdapter().capability(actor)


def prepare(row: dict) -> dict:
    if row != freeze():
        raise PilotStop("H03 manifest or runtime package changed")
    CredentialStore().inspect()
    if RUN_DIR.exists() or RUN_DIR.is_symlink() or any(
            actor_path(row, arm).exists() or actor_path(row, arm).is_symlink()
            for arm in ("B0", "S", "A")):
        raise PilotStop("H03 run or actor already exists")
    preview = Path(tempfile.mkdtemp(prefix="x5-h03-preflight-", dir=SEEDS))
    try:
        for name in row["actor_files"]:
            target = preview / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((SOURCE / name).read_bytes())
        preview_task = {"id": "H03", "actor_files": row["actor_files"],
                        "editable_paths": [EDITABLE],
                        "public_command": ["python3", "-B", "public_check.py"]}
        public = isolated_public_runner(preview_task)(
            ["python3", "-B", "public_check.py"], cwd=preview,
            capture_output=True, timeout=30, shell=False)
        if public.returncode == 0:
            raise PilotStop("H03 baseline no longer reproduces the public gap")
        controller_host(preview)
    finally:
        if preview.resolve().parent != SEEDS.resolve():
            raise PilotStop("H03 preflight cleanup escaped seeds")
        shutil.rmtree(preview)
    RUN_DIR.mkdir(parents=True)
    copy_actor(row, "B0", {name: (SOURCE / name).read_bytes() for name in row["actor_files"]})
    admit(row, "B0")
    verify_actor(row, "B0")
    exclusive(RUN_DIR / "prepared.json",
              {"manifest_sha256": row["manifest_sha256"],
               "producer_root_id": root_id(row, "B0"), "provider_calls": 0})
    return {"prepared": "B0", "root_id": root_id(row, "B0"), "provider_calls": 0}


def gate(row: dict, notice: dict) -> None:
    today = dt.datetime.now(dt.timezone.utc).astimezone(ZoneInfo("Australia/Sydney")).date().isoformat()
    if (row != freeze() or notice.get("approved") is not True
            or notice.get("manifest_sha256") != row["manifest_sha256"]
            or notice.get("maximum_usd") != TOTAL_LIMIT
            or notice.get("scope") != SCOPE
            or notice.get("date") != today
            or notice.get("provider") != "Claude.ai subscription through WSL"
            or notice.get("approval_source") !=
                "user explicitly approved H03b 52-file 879471-byte B0 payload and USD 16 cap"):
        raise PilotStop("dated H03 notice does not authorise this manifest and payload")


def ready(row: dict, arm: str) -> task_executor.TaskExecutor:
    executor = entry(row, arm)
    state = executor.status(root_id(row, arm))
    if (state["state"] != "ready" or state["attempts"]
            or state["budget"]["spent_usd"] != 0
            or state["budget"]["unresolved"] or state["budget"]["breached"]):
        raise PilotStop(f"H03 {arm} is not an unused settled root")
    verify_actor(row, arm)
    return executor


def public_risk(row: dict, actor: Path) -> dict:
    risk_path = FIXTURE / "risk_check.py"
    if risk_path.is_symlink() or not risk_path.is_file() or sha(risk_path.read_bytes()) != row["risk_check_sha256"]:
        raise PilotStop("H03 public risk check differs from frozen source")
    source = actor / EDITABLE
    if source.is_symlink() or not source.is_file():
        raise PilotStop("H03 accepted source is redirected")
    before = sha(source.read_bytes())
    wrapper = ("import runpy, sys\n"
               "sys.argv = ['risk_check.py', '--actor', '.']\n"
               "runpy.run_path('risk_check.py', run_name='__main__')\n").encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="h03-risk-", dir=SEEDS) as raw:
        isolated = Path(raw)
        files = {}
        for name, expected in row["actor_files"].items():
            if name == "public_check.py":
                continue
            path = actor / name
            if path.is_symlink() or not path.is_file():
                raise PilotStop(f"H03 accepted actor path is redirected: {name}")
            data = path.read_bytes()
            if name != EDITABLE and sha(data) != expected:
                raise PilotStop(f"H03 accepted actor protected file changed: {name}")
            target = isolated / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files[name] = sha(data)
        (isolated / "public_check.py").write_bytes(wrapper)
        (isolated / "risk_check.py").write_bytes(risk_path.read_bytes())
        files.update({"public_check.py": sha(wrapper),
                      "risk_check.py": row["risk_check_sha256"]})
        process = isolated_public_runner({"id": "H03-risk", "actor_files": files,
                                          "editable_paths": [EDITABLE]})(
            ["python3", "-B", "public_check.py"], cwd=isolated,
            capture_output=True, timeout=30, shell=False)
    if sha(source.read_bytes()) != before:
        raise PilotStop("H03 public risk check changed accepted source")
    stdout = process.stdout.decode("utf-8", errors="replace")
    stderr = process.stderr.decode("utf-8", errors="replace")
    lines = stdout.splitlines()
    observed = json.loads(lines[0]) if len(lines) == 1 else None
    criteria = ["fix the duplicate"]
    passed = (process.returncode == 0 and isinstance(observed, dict)
              and observed.get("schema_version") == 1 and observed.get("passed") is True
              and observed.get("outcome") == "solution"
              and observed.get("frames") == [criteria, criteria, criteria])
    qualified_failure = (process.returncode == 1 and isinstance(observed, dict)
                         and observed.get("schema_version") == 1 and observed.get("passed") is False
                         and observed.get("outcome") == "gap" and observed.get("framer_calls") == 3
                         and isinstance(observed.get("frames"), list)
                         and len(observed["frames"]) == 3
                         and observed["frames"][:2] == [criteria, criteria]
                         and observed["frames"][2] != criteria)
    return {"schema_version": 1, "source_sha256": before, "check_sha256": row["risk_check_sha256"],
            "passed": bool(passed), "qualified_failure": bool(qualified_failure),
            "observed": observed, "returncode": process.returncode,
            "isolation_evidence": process.isolation_evidence,
            "stderr_tail": stderr[-300:] if not (passed or qualified_failure) else ""}


def accepted_producer(state: dict) -> bool:
    if (state.get("state") != "accepted" or len(state.get("attempts", [])) != 1
            or state["budget"]["unresolved"] or state["budget"]["breached"]
            or not 0 < state["budget"]["spent_usd"] <= LIMITS["B0"]):
        return False
    attempt = state["attempts"][0]
    receipt = attempt.get("receipt") or {}
    verification = attempt.get("verification") or {}
    return (attempt.get("process_state") == "terminal"
            and receipt.get("terminal") is True
            and receipt.get("writer_stopped") is True
            and receipt.get("identity_valid") is True
            and receipt.get("actual_model") == "claude-sonnet-5"
            and receipt.get("cost_usd") == state["budget"]["spent_usd"]
            and verification.get("status") == "pass")


def edit_summary(actor: Path) -> str:
    before = (SOURCE / EDITABLE).read_text(encoding="utf-8").splitlines(keepends=True)
    after = (actor / EDITABLE).read_text(encoding="utf-8").splitlines(keepends=True)
    diff = list(difflib.unified_diff(before, after, n=1))
    added = sum(line.startswith("+") and not line.startswith("+++") for line in diff)
    removed = sum(line.startswith("-") and not line.startswith("---") for line in diff)
    if not (added or removed):
        raise PilotStop("accepted H03 producer made no source edit")
    return (f"Producer changed {EDITABLE}: {added} added and {removed} removed lines. "
            "The isolated public check passes. The separately frozen public risk report "
            "records a correctable critique re-entry gap; inspect that report before editing.")


def prepare_successors(row: dict, state: dict, risk_result: dict) -> dict:
    actor = actor_path(row, "B0")
    accepted = state["definition"]["acceptance_definition"]["contract"]
    contract_path = actor / ".claude/h03-acceptance.json"
    if contract_path.is_symlink() or not contract_path.is_file():
        raise PilotStop("H03 accepted contract is unavailable")
    contract_data = contract_path.read_bytes()
    if (accepted.get("rubric") != []
            or json.loads(contract_data) != {key: value for key, value in accepted.items()
                                             if key != "rubric"}):
        raise PilotStop("H03 accepted contract changed after admission")
    contract_data = (json.dumps(accepted, sort_keys=True) + "\n").encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="h03-checkpoint-", dir=SEEDS) as raw:
        checkpoint = Path(raw)
        for name, expected in row["actor_files"].items():
            source = actor / name
            if source.is_symlink() or not source.is_file():
                raise PilotStop(f"H03 accepted file is redirected: {name}")
            data = source.read_bytes()
            if name != EDITABLE and sha(data) != expected:
                raise PilotStop(f"H03 accepted protected file changed: {name}")
            target = checkpoint / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (checkpoint / "acceptance.json").write_bytes(contract_data)
        checkpoint_task = {"id": "H03-checkpoint",
                           "actor_files": {**row["actor_files"],
                                           "acceptance.json": sha(contract_data)},
                           "editable_paths": [EDITABLE]}
        record = review.twins(checkpoint, set(checkpoint_task["actor_files"]), state,
                              case()["risk"], case()["risk_digest"], RUN_DIR / "pair",
                              isolated_public_runner(checkpoint_task))
    summary = edit_summary(actor)
    review_record = review.write_review_goals(
        RUN_DIR / "pair", case()["risk"], case()["risk_digest"], summary)
    public_report = {**risk_result,
                     "public_recheck_command": "python3 -B risk_check.py --actor ."}
    report_data = (json.dumps(public_report, sort_keys=True, indent=2) + "\n").encode("utf-8")
    snapshots = []
    for arm in ("S", "A"):
        twin = RUN_DIR / "pair" / arm
        (twin / "RISK-REPORT.json").write_bytes(report_data)
        (twin / "risk_check.py").write_bytes((FIXTURE / "risk_check.py").read_bytes())
        files = {name: sha((twin / name).read_bytes())
                 for name in [*record["actor_sha256"], "REVIEW.md", "RISK-REPORT.json",
                              "risk_check.py"]}
        snapshots.append(files)
    if snapshots[0] != snapshots[1]:
        raise PilotStop("H03 successor public bytes differ")
    inputs = {"manifest_sha256": row["manifest_sha256"], "actor_files": snapshots[0],
              "risk_digest": case()["risk_digest"],
              "review_goal_sha256": review_record["review_goal_sha256"],
              "risk_report_sha256": sha(report_data)}
    exclusive(RUN_DIR / "pair/inputs.json", inputs)
    for arm in ("S", "A"):
        twin = RUN_DIR / "pair" / arm
        copy_actor(row, arm, {name: (twin / name).read_bytes() for name in snapshots[0]})
        if arm == "A":
            controller_host(actor_path(row, arm))
        admit(row, arm)
        verify_actor(row, arm)
    return {"snapshot": record, "inputs": inputs,
            "roots": {arm: root_id(row, arm) for arm in ("S", "A")}}


def producer(row: dict, notice: dict) -> dict:
    gate(row, notice)
    if load(RUN_DIR / "prepared.json").get("manifest_sha256") != row["manifest_sha256"]:
        raise PilotStop("H03 producer root belongs to another manifest")
    executor = ready(row, "B0")
    CredentialStore().inspect()
    exclusive(RUN_DIR / "producer-started.json",
              {"manifest_sha256": row["manifest_sha256"],
               "root_id": root_id(row, "B0")})
    error = None
    risk_result = None
    successors = None
    try:
        state = executor.run(root_id(row, "B0"), stop_after_attempts=1)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:400]
        state = executor.status(root_id(row, "B0"))
    if error is None and accepted_producer(state):
        try:
            risk_result = public_risk(row, actor_path(row, "B0"))
            exclusive(RUN_DIR / "risk-result.json", risk_result)
            if risk_result["qualified_failure"]:
                successors = prepare_successors(row, state, risk_result)
        except Exception as exc:
            error = type(exc).__name__ + ": " + str(exc)[:400]
    eligible = successors is not None
    result = {"manifest_sha256": row["manifest_sha256"],
              "root_id": root_id(row, "B0"), "state": state["state"],
              "budget": state["budget"], "attempt_count": len(state["attempts"]),
              "accepted_public_success": accepted_producer(state),
              "public_risk": risk_result, "eligible": eligible,
              "qualified": error is None and eligible, "successors": successors,
              "error": error}
    exclusive(RUN_DIR / "producer-result.json", result)
    return {"state": result["state"], "eligible": eligible,
            "spent_usd": state["budget"]["spent_usd"], "error": error}


def grade_actor(row: dict, arm: str) -> dict:
    actor = actor_path(row, arm)
    source = FIXTURE / "oracle.py"
    if source.is_symlink() or sha(source.read_bytes()) != row["oracle_sha256"]:
        raise PilotStop("H03 protected oracle changed")
    inventory = task(row, arm)["actor_files"]
    before = {}
    for name in inventory:
        path = actor / name
        if path.is_symlink() or not path.is_file():
            raise PilotStop(f"H03 grade source is redirected: {name}")
        before[name] = sha(path.read_bytes())
    with tempfile.TemporaryDirectory(prefix="h03-grade-", dir=SEEDS) as raw:
        candidate = Path(raw)
        for name in inventory:
            target = candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((actor / name).read_bytes())
        process = subprocess.run([sys.executable, "-B", str(source), "--actor", str(candidate)],
                                 cwd="/", capture_output=True, text=True,
                                 timeout=120, check=False)
    if process.returncode or len(process.stdout.splitlines()) != 1:
        raise PilotStop("H03 protected grade failed: " + process.stderr[-300:])
    result = json.loads(process.stdout)
    if (result.get("schema_version") != 2 or type(result.get("score")) is not int
            or not 0 <= result["score"] <= 100
            or type(result.get("critical_error")) is not bool):
        raise PilotStop("H03 protected grade has invalid shape")
    if before != {name: sha((actor / name).read_bytes()) for name in inventory}:
        raise PilotStop("H03 actor changed during protected grade")
    if sha(source.read_bytes()) != row["oracle_sha256"]:
        raise PilotStop("H03 protected oracle changed during grade")
    return result


def assessment_inputs(actor: Path) -> dict:
    lines = [line for line in (actor / "REVIEW.md").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    quotes = [{"source": "REVIEW.md", "quote": line} for line in lines]
    quotes.append({"source": "public_check.py", "quote":
        'scripted[("frame", "framer")] = [changed, canned["frame_v1"], canned["frame_v2"]]'})
    return {"issue": "REVIEW.md",
            "source_paths": ["REVIEW.md", "RISK-REPORT.json", "risk_check.py", "ISSUE.md",
                             "public_check.py", EDITABLE],
            "quote_requests": quotes,
            "operational": {"context_tokens": 1000, "deadline_seconds": None,
                            "prior_local_repairs": 1, "required_artefacts": [EDITABLE],
                            "deadline": None, "authorised_task_budget_usd": LIMITS["A"],
                            "observed_at": "2026-10-01T00:00:00Z"}}


def actionable_handoff(dispatch: dict | None) -> bool:
    handoff = dispatch.get("worker_handoff") if isinstance(dispatch, dict) else None
    if not isinstance(handoff, dict) or handoff.get("controller_used") is not True:
        return False
    findings = handoff.get("verified_findings")
    action = handoff.get("safe_next_action")
    return (isinstance(findings, list)
            and any(isinstance(item, dict)
                    and EDITABLE in str(item.get("source", ""))
                    and isinstance(item.get("text"), str) and item["text"].strip()
                    for item in findings)
            and isinstance(action, str) and len(action.strip()) >= 25
            and (EDITABLE in action or "public_check.py" in action))


def settled_result(row: dict, arm: str, state: dict, grade: dict | None,
                   error: str | None, workflow: dict | None, elapsed_s: float) -> dict:
    attempts = state["attempts"]
    identities = bool(attempts) and all(
        (attempt.get("receipt") or {}).get("identity_valid") is True
        and (attempt.get("receipt") or {}).get("terminal") is True
        and (attempt.get("receipt") or {}).get("writer_stopped") is True
        and (attempt.get("receipt") or {}).get("actual_model") == "claude-sonnet-5"
        and (attempt.get("process_state") == "terminal")
        for attempt in attempts)
    protected_stable = all(
        not (actor_path(row, arm) / name).is_symlink()
        and (actor_path(row, arm) / name).is_file()
        and sha((actor_path(row, arm) / name).read_bytes()) == expected
        for name, expected in task(row, arm)["actor_files"].items()
        if name != EDITABLE)
    dispatch = workflow.get("dispatch") if workflow else None
    decision = (state.get("routing_decision") or {}).get("decision") or {}
    role_budget = None
    if arm == "A" and dispatch and dispatch.get("controller_result"):
        role_dir = Path(dispatch["controller_result"].get("controller_run_dir", ""))
        if (role_dir.is_relative_to(actor_path(row, arm))
                and (role_dir / "dispatch-budget.json").is_file()):
            role_budget = dispatch_budget.DispatchBudget(
                role_dir / "dispatch-budget.json").snapshot()
    controller_ok = (arm == "S" or (
        decision.get("effective_action") == "controller"
        and isinstance(dispatch, dict) and dispatch.get("stage") == "worker-ready"
        and dispatch.get("controller_invocations") == 1
        and actionable_handoff(dispatch)
        and role_budget is not None and bool(role_budget["invocations"])
        and not role_budget["unresolved"]
        and not role_budget["breached"]
        and all(((call.get("telemetry") or {}).get("identity") or {}).get(
            "identity_valid") is True for call in role_budget["invocations"].values())))
    qualified = (error is None and grade is not None and identities and protected_stable
                 and len(attempts) == 1 and state["state"] in {"ready", "accepted"}
                 and not state["budget"]["unresolved"]
                 and not state["budget"]["breached"]
                 and 0 < state["budget"]["spent_usd"] <= LIMITS[arm]
                 and controller_ok)
    return {"manifest_sha256": row["manifest_sha256"], "case": "H03", "arm": arm,
            "root_id": root_id(row, arm), "state": state["state"],
            "attempt_count": len(attempts), "budget": state["budget"],
            "grade": grade, "qualified": qualified, "error": error,
            "worker_identity_valid": identities, "protected_stable": protected_stable,
            "effective_action": decision.get("effective_action"),
            "controller_stage": dispatch.get("stage") if dispatch else None,
            "controller_invocations": dispatch.get("controller_invocations") if dispatch else 0,
            "controller_handoff_actionable": actionable_handoff(dispatch) if arm == "A" else None,
            "elapsed_s": round(elapsed_s, 3)}


def continuation(row: dict, notice: dict, arm: str) -> dict:
    gate(row, notice)
    if arm not in {"S", "A"}:
        raise PilotStop("H03 continuation arm is invalid")
    producer_result = load(RUN_DIR / "producer-result.json")
    if (producer_result.get("manifest_sha256") != row["manifest_sha256"]
            or producer_result.get("qualified") is not True
            or load(RUN_DIR / "pair/inputs.json").get("manifest_sha256")
            != row["manifest_sha256"]):
        raise PilotStop("H03 successors lack an eligible public producer")
    if arm == "A" and load(RUN_DIR / "S-result.json").get("qualified") is not True:
        raise PilotStop("H03 S must settle before A")
    executor = ready(row, arm)
    actor = actor_path(row, arm)
    store = CredentialStore()
    store.inspect()
    if arm == "A":
        controller_dispatch.ControllerRuntimeAdapter().capability(actor)
    exclusive(RUN_DIR / f"{arm}-started.json",
              {"manifest_sha256": row["manifest_sha256"],
               "root_id": root_id(row, arm)})
    start = time.monotonic()
    workflow = None
    error = None
    session_name = None
    session_open = False
    original_env = dict(os.environ)
    try:
        if arm == "S":
            executor.run(root_id(row, arm), stop_after_attempts=1)
        else:
            session_name = "inv-" + uuid.uuid4().hex
            session = store.begin(session_name)
            clean = {key: value for key, value in os.environ.items()
                     if key not in {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                                    "CLAUDE_CODE_OAUTH_TOKEN", "WSLENV"}}
            clean["CLAUDE_CONFIG_DIR"] = str(session)
            clean["PATH"] = "/opt/orchestrator-worker-runtime/bin:" + clean.get("PATH", "")
            os.environ.clear()
            os.environ.update(clean)
            session_open = True
            inputs = assessment_inputs(actor)
            interpreter = WslPublicInterpreter(
                distro="kali-linux", linux_user="wsl", claude_path=screen.CLAUDE,
                launcher_path=str(ROOT / "tools/controller_wsl_launch.py"),
                allowance_usd=ASSESSMENT_LIMIT, runner=screen._local_runner)
            with hidden_evaluation_tree(ROOT):
                workflow = controller_workflow.execute(
                    executor, root_id(row, arm), interpreter=interpreter,
                    assessment_allowance_usd=ASSESSMENT_LIMIT,
                    controller_adapter=controller_dispatch.ControllerRuntimeAdapter(),
                    explicit_mode="on", public_passed=False,
                    worker_attempt_limit=1, defer_worker=True, **inputs)
            v7.settle_session(store, session_name)
            session_open = False
            os.environ.clear()
            os.environ.update(original_env)
            if ((workflow.get("decision") or {}).get("effective_action") == "controller"
                    and (workflow.get("dispatch") or {}).get("stage") == "worker-ready"):
                resumed = controller_workflow.execute(
                    executor, root_id(row, arm), interpreter=interpreter,
                    assessment_allowance_usd=ASSESSMENT_LIMIT,
                    controller_adapter=controller_dispatch.ControllerRuntimeAdapter(),
                    explicit_mode="on", public_passed=False,
                    worker_attempt_limit=1, defer_worker=False, **inputs)
                workflow = {**workflow, "task": resumed["task"]}
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:400]
    finally:
        if session_open:
            try:
                v7.settle_session(store, session_name)
                session_open = False
            except Exception as exc:
                error = (error + "; " if error else "") + "credential reconciliation: " + str(exc)[:250]
        os.environ.clear()
        os.environ.update(original_env)
    state = executor.status(root_id(row, arm))
    grade = None
    if not state["budget"]["unresolved"] and not session_open:
        try:
            grade = grade_actor(row, arm)
        except Exception as exc:
            error = (error + "; " if error else "") + "protected grade: " + str(exc)[:250]
    result = settled_result(row, arm, state, grade, error, workflow,
                            time.monotonic() - start)
    exclusive(RUN_DIR / f"{arm}-result.json", result)
    return {"arm": arm, "state": result["state"],
            "score": grade["score"] if grade else None,
            "spent_usd": state["budget"]["spent_usd"],
            "qualified": result["qualified"], "error": error}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--freeze", action="store_true")
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--producer", action="store_true")
    action.add_argument("--arm", choices=("S", "A"))
    args = parser.parse_args()
    if args.freeze:
        exclusive(MANIFEST_PATH, freeze())
        print(json.dumps({"manifest": str(MANIFEST_PATH), "provider_calls": 0}))
        return
    row = manifest()
    if args.prepare:
        print(json.dumps(prepare(row), sort_keys=True))
    elif args.producer:
        print(json.dumps(producer(row, load(NOTICE_PATH)), sort_keys=True))
    elif args.arm:
        print(json.dumps(continuation(row, load(NOTICE_PATH), args.arm), sort_keys=True))
    else:
        print(json.dumps({"manifest_sha256": row["manifest_sha256"],
                          "prepared": (RUN_DIR / "prepared.json").is_file(),
                          "producer_started": (RUN_DIR / "producer-started.json").is_file(),
                          "S_started": (RUN_DIR / "S-started.json").is_file(),
                          "A_started": (RUN_DIR / "A-started.json").is_file()}, sort_keys=True))


if __name__ == "__main__":
    main()
