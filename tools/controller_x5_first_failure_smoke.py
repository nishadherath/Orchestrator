#!/usr/bin/env python3
"""Single-use P02 engineering smoke for X5's first-failure handoff.

P02 is a known public canary. These calls test the live boundary and cannot
contribute to a prospective Controller uplift estimate. Freeze and prepare
are provider-free; each paid mode requires the exact approved notice.
"""

from __future__ import annotations

import argparse
import datetime as dt
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

import controller_campaign_manifest
import controller_dispatch
import controller_evaluation
import controller_public_assessment
import controller_workflow
import controller_x5_first_failure as checkpoint
import controller_x5_v6_screen as screen
import controller_x5_v7_pilot as v7
import dispatch_budget
import task_executor
from controller_wsl_interpreter import WslPublicInterpreter
from controller_x5_recovery_isolation import hidden_evaluation_tree
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import GRAFT, MCP, NODE, Q3WslAdapter, isolated_public_runner
from worker_wsl_q3_grade import grade


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "test/fixtures/worker_q2_public/P02/actor"
RUN_DIR = ROOT / "test/results/2026-09-30-controller-x5-first-failure-p02-smoke-run"
SCOPE = "P02 first-failure engineering smoke: one producer and conditional matched S/A calls"
PER_ROOT_USD = 5.0
MAXIMUM_USD = 15.0
ASSESSMENT_USD = 0.5
FOLLOW_ON_PROMPT = (
    "One bounded local repair after the settled first public failure. "
    "Run the public check and report truthful progress."
)


class SmokeStop(RuntimeError):
    """The single-use smoke cannot safely advance."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise SmokeStop(f"missing or redirected record: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def task() -> dict:
    catalogue = load(ROOT / "test/fixtures/worker_q2_public/catalogue.json")
    row = next((item for item in catalogue["tasks"] if item["id"] == "P02"), None)
    if row is None or len(row["editable_paths"]) != 2:
        raise SmokeStop("P02 catalogue contract is unavailable")
    for name, expected in row["actor_files"].items():
        path = SOURCE / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise SmokeStop(f"P02 source differs from catalogue: {name}")
    oracle = ROOT / "test/oracles/worker_q2_public/P02.json"
    if oracle.is_symlink() or not oracle.is_file() or sha(oracle.read_bytes()) != row["oracle_sha256"]:
        raise SmokeStop("P02 protected oracle differs from catalogue")
    return row


def freeze() -> dict:
    row = task()
    body = {"schema_version": 1, "stage": "x5-first-failure-p02-engineering-smoke",
            "case": "P02", "effect_unit": False,
            "actor_files": row["actor_files"], "editable_paths": row["editable_paths"],
            "oracle_sha256": row["oracle_sha256"],
            "schedule": ["B0", "S-if-public-failure", "A-if-S-qualified"],
            "worker_policy": "B0 first Sonnet-low call; one matched Sonnet-low continuation per arm",
            "per_root_maximum_usd": PER_ROOT_USD,
            "maximum_authorised_usd": MAXIMUM_USD,
            "assessment_allowance_usd": ASSESSMENT_USD,
            "controller_profile": "standard", "controller_invocations_per_A": 1,
            "eligibility": "one settled, writer-stopped, public-failed B0 attempt",
            "stop_rule": "stop on uncertainty, source drift, replay or invalid identity",
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "host": controller_campaign_manifest.host_record(),
            "credential_method": "claude-code-wsl-subscription"}
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def validate(manifest: dict) -> None:
    if manifest != freeze():
        raise SmokeStop("manifest or host/source package changed")


def gate(manifest: dict, notice: dict) -> None:
    validate(manifest)
    if (notice.get("approved") is not True
            or notice.get("manifest_sha256") != manifest["manifest_sha256"]
            or notice.get("maximum_usd") != MAXIMUM_USD
            or notice.get("scope") != SCOPE
            or not isinstance(notice.get("date"), str)
            or not isinstance(notice.get("approval_source"), str)):
        raise SmokeStop("dated cost notice does not authorise this manifest")


def actor_path(manifest: dict, arm: str) -> Path:
    if arm not in {"B0", "S", "A"}:
        raise SmokeStop("unknown smoke arm")
    return SEEDS / f"x5-first-failure-{manifest['manifest_sha256'][:12]}-p02-{arm.lower()}"


def root_id(manifest: dict, arm: str) -> str:
    return controller_evaluation.digest(
        {"manifest": manifest["manifest_sha256"], "case": "P02", "arm": arm})[:24]


def expected_files(manifest: dict, arm: str) -> dict[str, str]:
    if arm == "B0":
        return manifest["actor_files"]
    record = load(RUN_DIR / "pair/snapshot.json")
    if record.get("producer_root_id") != root_id(manifest, "B0"):
        raise SmokeStop("successor snapshot belongs to another producer")
    return record["actor_sha256"]


def verify_actor(manifest: dict, arm: str) -> None:
    actor = actor_path(manifest, arm)
    for name, expected in expected_files(manifest, arm).items():
        path = actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise SmokeStop(f"actor changed before dispatch: {arm}/{name}")


def entry(manifest: dict, arm: str) -> task_executor.TaskExecutor:
    actor = actor_path(manifest, arm)
    row = task()
    return task_executor.TaskExecutor(
        actor, Q3WslAdapter(row), command_runner=isolated_public_runner(row),
        campaign_prompt=None if arm == "B0" else FOLLOW_ON_PROMPT)


def admit(manifest: dict, arm: str) -> None:
    actor = actor_path(manifest, arm)
    editable = manifest["editable_paths"]
    protected = sorted(set(manifest["actor_files"]) - set(editable))
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only the two declared source files may change"],
                "required_outputs": editable, "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = actor / ".claude/x5-first-failure-acceptance.json"
    contract_path.parent.mkdir(exist_ok=True)
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    rid = root_id(manifest, arm)
    entry(manifest, arm).admit(
        goal=(actor / "ISSUE.md").read_text(encoding="utf-8"),
        scope=editable, permissions=["read", "edit"], input_paths=protected,
        acceptance_path=contract_path, budget_usd=PER_ROOT_USD,
        authority_id=controller_evaluation.digest({"root": rid, "grant": "x5-first-failure"})[:32],
        actor="x5-first-failure-smoke", root_id=rid, task_id=f"p02-{arm.lower()}")


def copy_actor(manifest: dict, arm: str, source_files: dict[str, bytes]) -> None:
    actor = actor_path(manifest, arm)
    if actor.exists() or actor.is_symlink():
        raise SmokeStop("single-use actor path already exists")
    actor.mkdir(mode=0o700)
    for name, data in source_files.items():
        path = actor / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def build_controller_graph(actor: Path) -> None:
    config = actor / ".mcp.json"
    config.write_bytes(MCP.read_bytes())
    config.chmod(0o600)
    graph = subprocess.run([str(NODE), str(GRAFT), "build", str(actor)],
                           cwd=actor, capture_output=True, text=True,
                           timeout=120, check=False)
    if graph.returncode or not (actor / "graft").is_dir():
        raise SmokeStop("Controller Graft preflight failed: " + graph.stderr[-300:])
    controller_dispatch.ControllerRuntimeAdapter().capability(actor)


def prepare(manifest: dict) -> dict:
    validate(manifest)
    CredentialStore().inspect()
    if RUN_DIR.exists() or RUN_DIR.is_symlink():
        raise SmokeStop("single-use run directory already exists")
    preview = Path(tempfile.mkdtemp(prefix="x5-first-failure-preflight-", dir=SEEDS))
    try:
        for name in manifest["actor_files"]:
            path = preview / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((SOURCE / name).read_bytes())
        build_controller_graph(preview)
    finally:
        if preview.resolve().parent != SEEDS.resolve():
            raise SmokeStop("preflight cleanup path escaped seed root")
        shutil.rmtree(preview)
    RUN_DIR.mkdir(parents=True)
    copy_actor(manifest, "B0", {name: (SOURCE / name).read_bytes()
                                for name in manifest["actor_files"]})
    admit(manifest, "B0")
    exclusive(RUN_DIR / "prepared.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "producer_root_id": root_id(manifest, "B0"), "provider_calls": 0})
    return {"producer_root_id": root_id(manifest, "B0"), "provider_calls": 0}


def require_ready(manifest: dict, arm: str) -> task_executor.TaskExecutor:
    executor = entry(manifest, arm)
    state = executor.status(root_id(manifest, arm))
    if (state["state"] != "ready" or state["attempts"]
            or state["budget"]["spent_usd"] != 0
            or state["budget"]["unresolved"]
            or state["budget"]["limit_usd"] != PER_ROOT_USD):
        raise SmokeStop("single-use root is not ready")
    return executor


def prepare_successors(manifest: dict, state: dict) -> dict:
    row = task()
    record = checkpoint.twins(
        actor_path(manifest, "B0"), set(manifest["actor_files"]), state,
        RUN_DIR / "pair", isolated_public_runner(row))
    for arm in ("S", "A"):
        files = {name: (RUN_DIR / "pair" / arm / name).read_bytes()
                 for name in record["actor_sha256"]}
        if {name: sha(data) for name, data in files.items()} != record["actor_sha256"]:
            raise SmokeStop("successor snapshot changed")
        copy_actor(manifest, arm, files)
        if arm == "A":
            build_controller_graph(actor_path(manifest, arm))
        admit(manifest, arm)
    return record


def protected_grade(actor: Path, state: dict) -> dict | None:
    if state["budget"]["unresolved"] or not state["attempts"]:
        return None
    label = "partial" if state["state"] == "ready" else state["state"]
    if label not in {"accepted", "partial", "failed"}:
        return None
    return grade(ROOT, actor, "P02", label)


def producer(manifest: dict, notice: dict) -> dict:
    gate(manifest, notice)
    if load(RUN_DIR / "prepared.json")["manifest_sha256"] != manifest["manifest_sha256"]:
        raise SmokeStop("prepared producer differs from manifest")
    executor = require_ready(manifest, "B0")
    verify_actor(manifest, "B0")
    CredentialStore().inspect()
    exclusive(RUN_DIR / "producer-started.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "root_id": root_id(manifest, "B0")})
    start = time.monotonic()
    error = None
    snapshot = None
    try:
        state = executor.run(root_id(manifest, "B0"), stop_after_attempts=1)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:400]
        state = executor.status(root_id(manifest, "B0"))
    if error is None and state["state"] == "ready":
        try:
            snapshot = prepare_successors(manifest, state)
        except (checkpoint.CheckpointStop, SmokeStop) as exc:
            error = str(exc)
    grade_value = None
    if not state["budget"]["unresolved"]:
        try:
            grade_value = protected_grade(actor_path(manifest, "B0"), state)
        except Exception as exc:
            error = (error + "; " if error else "") + "protected grade: " + str(exc)[:250]
    eligible = snapshot is not None
    qualified = (error is None and grade_value is not None
                 and not state["budget"]["unresolved"]
                 and not state["budget"]["breached"]
                 and state["budget"]["spent_usd"] <= PER_ROOT_USD
                 and (eligible or state["state"] == "accepted"))
    result = {"manifest_sha256": manifest["manifest_sha256"],
              "root_id": root_id(manifest, "B0"), "state": state["state"],
              "budget": state["budget"], "attempt_count": len(state["attempts"]),
              "eligible": eligible, "qualified": qualified,
              "snapshot": snapshot, "error": error,
              "protected_grade_after_public_entry": grade_value,
              "elapsed_s": round(time.monotonic() - start, 3)}
    exclusive(RUN_DIR / "producer-result.json", result)
    return {"eligible": eligible, "qualified": qualified,
            "state": state["state"], "spent_usd": state["budget"]["spent_usd"],
            "error": error}


def assessment_inputs(actor: Path) -> dict:
    issue = (actor / "ISSUE.md").read_text(encoding="utf-8")
    public = (actor / "public_check.py").read_text(encoding="utf-8")
    heading = next(line for line in issue.splitlines() if line.startswith("# "))
    examples = [line for line in public.splitlines()
                if "self.assertTrue(token.startswith" in line
                or "with self.assertRaises(SignatureExpired)" in line]
    if len(examples) != 2 or any(public.count(line) != 1 for line in examples):
        raise SmokeStop("public assessment citations changed")
    return {"issue": "ISSUE.md",
            "source_paths": ["ISSUE.md", "public_check.py", "itsdangerous/timed.py",
                             "itsdangerous/url_safe.py", "itsdangerous/serializer.py"],
            "quote_requests": [{"source": "ISSUE.md", "quote": heading}]
                              + [{"source": "public_check.py", "quote": line}
                                 for line in examples],
            "operational": {"context_tokens": 1000, "deadline_seconds": None,
                            "prior_local_repairs": 1,
                            "required_artefacts": load(actor / "acceptance.json")["editable_paths"],
                            "deadline": None, "authorised_task_budget_usd": PER_ROOT_USD,
                            "observed_at": dt.datetime.now(dt.timezone.utc).isoformat()}}


def actionable_handoff(dispatch: dict | None) -> bool:
    handoff = dispatch.get("worker_handoff") if isinstance(dispatch, dict) else None
    if not isinstance(handoff, dict) or handoff.get("controller_used") is not True:
        return False
    editable = set(task()["editable_paths"])
    findings = handoff.get("verified_findings")
    if not isinstance(findings, list) or not any(
            isinstance(row, dict) and isinstance(row.get("source"), str)
            and isinstance(row.get("text"), str) and row["text"].strip()
            and any(name in row["source"] for name in editable)
            for row in findings):
        return False
    action = handoff.get("safe_next_action")
    return (isinstance(action, str) and len(action.strip()) >= 25
            and "restore the frozen acceptance criteria" not in action.lower()
            and any(name in action for name in editable | {"public_check.py"}))


def continuation(manifest: dict, notice: dict, arm: str) -> dict:
    gate(manifest, notice)
    if arm not in {"S", "A"}:
        raise SmokeStop("unknown successor arm")
    producer_result = load(RUN_DIR / "producer-result.json")
    if (producer_result.get("manifest_sha256") != manifest["manifest_sha256"]
            or producer_result.get("eligible") is not True
            or producer_result.get("qualified") is not True
            or producer_result.get("snapshot") != load(RUN_DIR / "pair/snapshot.json")):
        raise SmokeStop("producer checkpoint or twin snapshot changed")
    if arm == "A" and load(RUN_DIR / "S-result.json").get("qualified") is not True:
        raise SmokeStop("settled S result is required before A")
    executor = require_ready(manifest, arm)
    verify_actor(manifest, arm)
    actor = actor_path(manifest, arm)
    store = CredentialStore()
    store.inspect()
    if arm == "A":
        controller_dispatch.ControllerRuntimeAdapter().capability(actor)
    exclusive(RUN_DIR / f"{arm}-started.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "root_id": root_id(manifest, arm)})
    start = time.monotonic()
    environment = dict(os.environ)
    session_name = None
    session_open = False
    workflow = None
    error = None
    try:
        if arm == "A":
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
            worker = executor.adapter
            original_run = worker.run

            def run_worker(request):
                nonlocal session_open
                if session_open:
                    v7.settle_session(store, session_name)
                    session_open = False
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
                try:
                    return original_run(request)
                finally:
                    os.environ["CLAUDE_CONFIG_DIR"] = str(session)

            worker.run = run_worker
        if arm == "S":
            executor.run(root_id(manifest, arm), stop_after_attempts=1)
        else:
            interpreter = WslPublicInterpreter(
                distro="kali-linux", linux_user="wsl", claude_path=screen.CLAUDE,
                launcher_path=str(ROOT / "tools/controller_wsl_launch.py"),
                allowance_usd=ASSESSMENT_USD, runner=screen._local_runner)
            with hidden_evaluation_tree(ROOT):
                workflow = controller_workflow.execute(
                    executor, root_id(manifest, arm), interpreter=interpreter,
                    assessment_allowance_usd=ASSESSMENT_USD,
                    controller_adapter=controller_dispatch.ControllerRuntimeAdapter(),
                    explicit_mode="on", public_passed=False,
                    worker_attempt_limit=1, **assessment_inputs(actor))
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
        os.environ.update(environment)
    state = executor.status(root_id(manifest, arm))
    grade_value = None
    if not state["budget"]["unresolved"] and not session_open:
        try:
            grade_value = protected_grade(actor, state)
        except Exception as exc:
            error = (error + "; " if error else "") + "protected grade: " + str(exc)[:250]
    decision = (state.get("routing_decision") or {}).get("decision") or {}
    dispatch = workflow.get("dispatch") if workflow else None
    actionable = actionable_handoff(dispatch) if arm == "A" else None
    role_budget = None
    if dispatch and dispatch.get("controller_result"):
        role_dir = Path(dispatch["controller_result"].get("controller_run_dir", ""))
        if role_dir.is_relative_to(actor) and (role_dir / "dispatch-budget.json").is_file():
            role_budget = dispatch_budget.DispatchBudget(
                role_dir / "dispatch-budget.json").snapshot()
    attempts = state["attempts"]
    identities_valid = all(
        (attempt.get("receipt") or {}).get("identity_valid") is True
        and (attempt.get("receipt") or {}).get("actual_model") == "claude-sonnet-5"
        and (attempt.get("receipt") or {}).get("writer_stopped") is True
        for attempt in attempts)
    qualified = (error is None and grade_value is not None and len(attempts) == 1
                 and identities_valid and state["state"] in {"ready", "accepted"}
                 and not state["budget"]["unresolved"] and not state["budget"]["breached"]
                 and state["budget"]["spent_usd"] <= PER_ROOT_USD
                 and (arm == "S" or (
                     decision.get("effective_action") == "controller"
                     and dispatch is not None and dispatch.get("stage") == "worker-ready"
                     and dispatch.get("controller_invocations") == 1
                     and actionable is True and role_budget is not None
                     and not role_budget["unresolved"] and not role_budget["breached"])))
    result = {"manifest_sha256": manifest["manifest_sha256"], "arm": arm,
              "root_id": root_id(manifest, arm), "state": state["state"],
              "budget": state["budget"], "attempt_count": len(attempts),
              "grade": grade_value, "effective_action": decision.get("effective_action"),
              "controller_stage": dispatch.get("stage") if dispatch else None,
              "controller_invocations": dispatch.get("controller_invocations") if dispatch else 0,
              "controller_handoff_actionable": actionable,
              "controller_role_cost_usd": role_budget["spent_usd"] if role_budget else None,
              "worker_identity_valid": identities_valid, "qualified": qualified,
              "error": error, "credential_reconciled": not session_open,
              "elapsed_s": round(time.monotonic() - start, 3)}
    exclusive(RUN_DIR / f"{arm}-result.json", result)
    return {"arm": arm, "state": state["state"],
            "spent_usd": state["budget"]["spent_usd"],
            "quality": grade_value["quality"] if grade_value else None,
            "qualified": qualified, "error": error}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "prepare", "producer", "continuation"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--notice", type=Path)
    parser.add_argument("--arm", choices=("S", "A"))
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() != 0:
        raise SmokeStop("smoke driver requires attested WSL root")
    if args.mode == "freeze":
        exclusive(args.manifest, freeze())
        print(json.dumps({"manifest_sha256": load(args.manifest)["manifest_sha256"]}))
        return
    manifest = load(args.manifest)
    if args.mode == "prepare":
        result = prepare(manifest)
    else:
        if args.notice is None:
            raise SmokeStop("paid mode requires an exact dated cost notice")
        notice = load(args.notice)
        if args.mode == "producer":
            result = producer(manifest, notice)
        else:
            if args.arm is None:
                raise SmokeStop("continuation needs S or A")
            result = continuation(manifest, notice, args.arm)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
