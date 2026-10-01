#!/usr/bin/env python3
"""Single-use matched S/A continuation from H02c's settled public failure."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

import controller_campaign_manifest
import controller_dispatch
import controller_evaluation
import controller_workflow
import model_registry
import controller_x5_h02_grade as grader
import controller_x5_v6_screen as screen
import controller_x5_v7_pilot as v7
import dispatch_budget
import task_executor
from controller_wsl_interpreter import WslPublicInterpreter
from controller_x5_recovery_isolation import hidden_evaluation_tree
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import GRAFT, MCP, NODE
from worker_wsl_q4u_adapter import Q4UWslAdapter, isolated_public_runner


ROOT = Path(__file__).resolve().parents[1]
PRODUCER_MANIFEST = ROOT / "test/results/2026-09-30-controller-x5-h02c-producer-manifest.json"
PRODUCER_RUN = ROOT / "test/results/2026-09-30-controller-x5-h02c-producer-run"
MANIFEST_PATH = ROOT / "test/results/2026-09-30-controller-x5-h02-sa-manifest.json"
RUN_DIR = ROOT / "test/results/2026-09-30-controller-x5-h02-sa-run"
CATALOGUE = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02/catalogue-h02.json"
SCOPE = "H02 public-failure matched S/A continuation: one worker call per arm and one Controller admission"
ROOT_LIMITS = {"S": 4.0, "A": 6.0}
TOTAL_LIMIT = 10.0
ASSESSMENT_LIMIT = 0.5
PROMPT = "Investigate the public failure, verify distinct causes and report truthful progress."
EDITABLE = "pytest_asyncio/plugin.py"


class PairStop(RuntimeError):
    """The frozen H02 comparison cannot safely advance."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise PairStop(f"missing or redirected record: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def producer_snapshot() -> dict:
    """Use only public verification and settled receipts for eligibility."""
    source = load(PRODUCER_MANIFEST)
    result = load(PRODUCER_RUN / "producer-result.json")
    actor = SEEDS / f"x5-h02c-{source['manifest_sha256'][:16]}-b0"
    state = task_executor.TaskExecutor(actor, None).status(result["root_id"])
    if (result.get("manifest_sha256") != source["manifest_sha256"]
            or result.get("root_id") != state["root_id"]
            or state["state"] != "ready" or len(state["attempts"]) != 1
            or state["budget"]["unresolved"] or state["budget"]["breached"]
            or not 0 < state["budget"]["spent_usd"] <= 4.0):
        raise PairStop("H02c producer is not a settled single public failure")
    attempt = state["attempts"][0]
    receipt = attempt.get("receipt") or {}
    verification = attempt.get("verification") or {}
    if (attempt.get("process_state") != "terminal"
            or receipt.get("terminal") is not True
            or receipt.get("writer_stopped") is not True
            or receipt.get("identity_valid") is not True
            or model_registry.model_class_for_provider_id(
                receipt.get("actual_model")) != "sonnet"
            or receipt.get("cost_usd") != state["budget"]["spent_usd"]
            or verification.get("status") != "fail"):
        raise PairStop("H02c public attempt or identity is not eligible")
    catalogue = load(CATALOGUE)
    if source["catalogue_sha256"] != catalogue["catalogue_sha256"]:
        raise PairStop("H02 catalogue changed after producer")
    files = {}
    for name, expected in source["actor_files"].items():
        path = actor / name
        if path.is_symlink() or not path.is_file():
            raise PairStop(f"H02c public snapshot file is unsafe: {name}")
        value = sha(path.read_bytes())
        if name != EDITABLE and value != expected:
            raise PairStop(f"H02c protected source changed: {name}")
        files[name] = value
    if files[EDITABLE] == source["actor_files"][EDITABLE]:
        raise PairStop("H02c worker made no editable revision")
    return {"schema_version": 1, "producer_manifest_sha256": source["manifest_sha256"],
            "producer_result_sha256": sha((PRODUCER_RUN / "producer-result.json").read_bytes()),
            "producer_root_id": result["root_id"],
            "producer_cost_usd": state["budget"]["spent_usd"],
            "producer_model": receipt["actual_model"],
            "public_verification": "fail", "actor_files": dict(sorted(files.items()))}


def freeze() -> dict:
    catalogue = load(CATALOGUE)
    snapshot = producer_snapshot()
    body = {"schema_version": 1, "stage": "x5-h02-public-failure-matched-sa",
            "case_id": "H02", "origin": "authored development adaptation",
            "snapshot": snapshot, "catalogue_sha256": catalogue["catalogue_sha256"],
            "grader_sha256": sha(Path(grader.__file__).read_bytes()),
            "editable_paths": [EDITABLE], "schedule": ["S", "A"],
            "root_limits_usd": ROOT_LIMITS,
            "maximum_authorised_usd": TOTAL_LIMIT,
            "assessment_allowance_usd": ASSESSMENT_LIMIT,
            "worker_policy": "one Sonnet-low Q4U attempt from identical bytes in each arm",
            "controller_profile": "standard", "controller_invocations_per_A": 1,
            "analysis_rule": "primary uplift only if A is accepted at quality 100 and S is not; also report A minus S quality",
            "eligibility_rule": "settled identity-valid H02c public verification failed; hidden grade unused",
            "stop_rule": "stop on uncertainty, source drift, replay, invalid identity or budget breach",
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "host": controller_campaign_manifest.host_record(),
            "credential_method": "claude-code-wsl-subscription"}
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def manifest() -> dict:
    saved = load(MANIFEST_PATH)
    if saved != freeze():
        raise PairStop("H02 S/A manifest or runtime package changed")
    return saved


def gate(row: dict, notice: dict) -> None:
    if (notice.get("approved") is not True
            or notice.get("manifest_sha256") != row["manifest_sha256"]
            or notice.get("maximum_usd") != TOTAL_LIMIT
            or notice.get("scope") != SCOPE
            or notice.get("date") != "2026-09-30"
            or not isinstance(notice.get("approval_source"), str)):
        raise PairStop("dated H02 S/A notice does not authorise this manifest")


def actor_path(row: dict, arm: str) -> Path:
    return SEEDS / f"x5-h02-sa-{row['manifest_sha256'][:16]}-{arm.lower()}"


def root_id(row: dict, arm: str) -> str:
    return controller_evaluation.digest({"manifest": row["manifest_sha256"],
                                         "case": "H02", "arm": arm})[:24]


def task(row: dict) -> dict:
    return {"id": "H02", "actor_files": row["snapshot"]["actor_files"],
            "editable_paths": [EDITABLE]}


def entry(row: dict, arm: str) -> task_executor.TaskExecutor:
    contract = task(row)
    return task_executor.TaskExecutor(
        actor_path(row, arm), Q4UWslAdapter(contract),
        command_runner=isolated_public_runner(contract),
        campaign_prompt=PROMPT)


def admission(row: dict, arm: str) -> None:
    actor = actor_path(row, arm)
    files = row["snapshot"]["actor_files"]
    protected = sorted(set(files) - {EDITABLE})
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only pytest_asyncio/plugin.py may change"],
                "required_outputs": [EDITABLE], "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = actor / ".claude/h02-sa-acceptance.json"
    contract_path.parent.mkdir(exist_ok=True)
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    rid = root_id(row, arm)
    entry(row, arm).admit(
        goal=(actor / "ISSUE.md").read_text(encoding="utf-8"),
        scope=[EDITABLE], permissions=["read", "edit"], input_paths=protected,
        acceptance_path=contract_path, budget_usd=ROOT_LIMITS[arm],
        authority_id=controller_evaluation.digest(
            {"root": rid, "grant": "x5-h02-sa"})[:32],
        actor="x5-h02-matched-development", root_id=rid,
        task_id=f"h02-{arm.lower()}")


def verify_initial(row: dict, arm: str) -> None:
    actor = actor_path(row, arm)
    for name, expected in row["snapshot"]["actor_files"].items():
        path = actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise PairStop(f"H02 {arm} initial public file changed: {name}")


def controller_host(actor: Path) -> None:
    config = actor / ".mcp.json"
    config.write_bytes(MCP.read_bytes())
    config.chmod(0o600)
    graph = subprocess.run([str(NODE), str(GRAFT), "build", str(actor)],
                           cwd=actor, capture_output=True, text=True,
                           timeout=120, check=False)
    if graph.returncode or not (actor / "graft").is_dir():
        raise PairStop("H02 Controller Graft build failed: " + graph.stderr[-300:])
    controller_dispatch.ControllerRuntimeAdapter().capability(actor)


def prepare(row: dict) -> dict:
    CredentialStore().inspect()
    if RUN_DIR.exists() or RUN_DIR.is_symlink() or any(
            actor_path(row, arm).exists() or actor_path(row, arm).is_symlink()
            for arm in ("S", "A")):
        raise PairStop("H02 S/A run or root already exists")
    original = SEEDS / (f"x5-h02c-"
                        f"{row['snapshot']['producer_manifest_sha256'][:16]}-b0")
    public = isolated_public_runner(task(row))(
        ["python3", "-B", "public_check.py"], cwd=original,
        capture_output=True, timeout=30, shell=False)
    if public.returncode != 1:
        raise PairStop("H02 source no longer has a public failure")
    for arm in ("S", "A"):
        actor = actor_path(row, arm)
        actor.mkdir(mode=0o700)
        for name, expected in row["snapshot"]["actor_files"].items():
            data = (original / name).read_bytes()
            if sha(data) != expected:
                raise PairStop(f"H02c snapshot changed before {arm} copy: {name}")
            target = actor / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if arm == "A":
            controller_host(actor)
        admission(row, arm)
    verify_initial(row, "S")
    verify_initial(row, "A")
    RUN_DIR.mkdir(parents=True)
    exclusive(RUN_DIR / "snapshot.json", row["snapshot"])
    exclusive(RUN_DIR / "prepared.json",
              {"manifest_sha256": row["manifest_sha256"],
               "roots": {arm: root_id(row, arm) for arm in ("S", "A")},
               "provider_calls": 0})
    return {"prepared": ["S", "A"], "provider_calls": 0,
            "source_plugin_sha256": row["snapshot"]["actor_files"][EDITABLE]}


def ready(row: dict, arm: str) -> task_executor.TaskExecutor:
    result = entry(row, arm)
    state = result.status(root_id(row, arm))
    if (state["state"] != "ready" or state["attempts"]
            or state["budget"]["spent_usd"] != 0
            or state["budget"]["unresolved"]
            or state["budget"]["limit_usd"] != ROOT_LIMITS[arm]):
        raise PairStop(f"H02 {arm} root is not fresh and ready")
    verify_initial(row, arm)
    return result


def grade_actor(row: dict, arm: str) -> dict:
    actor = actor_path(row, arm)
    before = {name: sha((actor / name).read_bytes())
              for name in row["snapshot"]["actor_files"]}
    with tempfile.TemporaryDirectory(prefix="h02-sa-grade-", dir=SEEDS) as raw:
        candidate = Path(raw)
        for name in before:
            target = candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((actor / name).read_bytes())
        result = grader.grade(candidate)
    if before != {name: sha((actor / name).read_bytes()) for name in before}:
        raise PairStop(f"H02 {arm} actor changed during grading")
    return result


def assessment_inputs(actor: Path) -> dict:
    issue_lines = [line for line in (actor / "ISSUE.md").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    assertions = [line for line in (actor / "case/test_mre.py").read_text(
        encoding="utf-8").splitlines() if line.lstrip().startswith("assert ")]
    quotes = ([{"source": "ISSUE.md", "quote": line} for line in issue_lines]
              + [{"source": "case/test_mre.py", "quote": line}
                 for line in assertions])
    return {"issue": "ISSUE.md",
            "source_paths": ["ISSUE.md", "case/test_mre.py",
                             "case/conftest.py", "public_check.py"],
            "quote_requests": quotes,
            "operational": {"context_tokens": 1000, "deadline_seconds": None,
                            "prior_local_repairs": 1,
                            "required_artefacts": [EDITABLE], "deadline": None,
                            "authorised_task_budget_usd": ROOT_LIMITS["A"],
                            "observed_at": "2026-09-30T00:00:00Z"}}


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
                   error: str | None, workflow: dict | None,
                   elapsed_s: float) -> dict:
    attempts = state["attempts"]
    identities = bool(attempts) and all(
        (attempt.get("receipt") or {}).get("identity_valid") is True
        and (attempt.get("receipt") or {}).get("terminal") is True
        and (attempt.get("receipt") or {}).get("writer_stopped") is True
        for attempt in attempts)
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
        and role_budget is not None and not role_budget["unresolved"]
        and not role_budget["breached"]
        and all(((call.get("telemetry") or {}).get("identity") or {}).get(
            "identity_valid") is True for call in role_budget["invocations"].values())))
    qualified = (error is None and grade is not None and identities
                 and len(attempts) == 1 and state["state"] in {"ready", "accepted"}
                 and not state["budget"]["unresolved"]
                 and not state["budget"]["breached"]
                 and 0 < state["budget"]["spent_usd"] <= ROOT_LIMITS[arm]
                 and controller_ok)
    return {"manifest_sha256": row["manifest_sha256"], "case": "H02",
            "arm": arm, "root_id": root_id(row, arm), "state": state["state"],
            "attempt_count": len(attempts), "budget": state["budget"],
            "grade": grade, "qualified": qualified, "error": error,
            "worker_identity_valid": identities,
            "effective_action": decision.get("effective_action"),
            "controller_stage": dispatch.get("stage") if dispatch else None,
            "controller_invocations": dispatch.get("controller_invocations") if dispatch else 0,
            "controller_handoff_actionable": (
                actionable_handoff(dispatch) if arm == "A" else None),
            "elapsed_s": round(elapsed_s, 3)}


def continuation(row: dict, notice: dict, arm: str) -> dict:
    gate(row, notice)
    if arm not in {"S", "A"}:
        raise PairStop("H02 continuation arm is invalid")
    if load(RUN_DIR / "prepared.json")["manifest_sha256"] != row["manifest_sha256"]:
        raise PairStop("H02 prepared pair belongs to another manifest")
    if load(RUN_DIR / "snapshot.json") != row["snapshot"]:
        raise PairStop("H02 twin public snapshot changed")
    if arm == "A" and load(RUN_DIR / "S-result.json").get("qualified") is not True:
        raise PairStop("H02 S result must settle before A")
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
            "quality": grade["quality"] if grade else None,
            "spent_usd": state["budget"]["spent_usd"],
            "qualified": result["qualified"], "error": error}


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise PairStop("H02 S/A requires WSL root")
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze", action="store_true")
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--arm", choices=("S", "A"))
    parser.add_argument("--notice", type=Path)
    args = parser.parse_args()
    if args.freeze:
        exclusive(MANIFEST_PATH, freeze())
        result = {"manifest_sha256": load(MANIFEST_PATH)["manifest_sha256"],
                  "provider_calls": 0}
    elif args.prepare:
        result = prepare(manifest())
    else:
        if args.notice is None:
            raise PairStop("dated H02 S/A cost notice required")
        result = continuation(manifest(), load(args.notice), args.arm)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
