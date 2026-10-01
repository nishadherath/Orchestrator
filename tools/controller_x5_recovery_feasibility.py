#!/usr/bin/env python3
"""Single-use, paired X5 recovery feasibility on the attested WSL host.

Freeze and prepare are provider-free. Producer and successor modes require an
exact dated notice. A started marker is never removed or replayed.
"""

from __future__ import annotations

import argparse
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
import dispatch_budget
import controller_x5_recovery_grade
from controller_x5_recovery_isolation import hidden_evaluation_tree
import controller_x5_recovery_protocol as protocol
import controller_x5_v6_screen as screen
import controller_x5_v7_pilot as v7
import task_executor
from controller_wsl_interpreter import WslPublicInterpreter
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import GRAFT, MCP, NODE, isolated_public_runner


ROOT = Path(__file__).resolve().parents[1]
CASES = ("R01", "R02")
RUN_DIR = ROOT / "test/results/2026-09-29-controller-x5-recovery-feasibility-r3-run"
SCOPE = "two X5 recovery producers and up to four matched development continuations"
PER_ROOT_USD = 5.0
MAXIMUM_USD = 30.0
ASSESSMENT_USD = 0.5
PROMPT = "Investigate the public failure, verify distinct causes and report truthful progress."


class FeasibilityStop(RuntimeError):
    """A frozen run cannot safely advance."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise FeasibilityStop(f"missing or redirected record: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def source(task_id: str) -> Path:
    return ROOT / "test/fixtures/controller_x5_recovery/development" / task_id / "actor"


def oracle(task_id: str) -> Path:
    return ROOT / "test/oracles/controller_x5_recovery" / f"{task_id}.json"


def package(task_id: str) -> dict:
    files = protocol.public_files(source(task_id), task_id)
    protected = oracle(task_id)
    if protected.is_symlink() or not protected.is_file():
        raise FeasibilityStop("protected oracle is missing or redirected")
    return {"actor_files": {name: sha(data) for name, data in sorted(files.items())},
            "oracle_sha256": sha(protected.read_bytes())}


def freeze() -> dict:
    body = {"schema_version": 1, "stage": "x5-recovery-development-feasibility",
            "cases": list(CASES), "packages": {task: package(task) for task in CASES},
            "schedule": [{"task_id": task, "producer": "B0",
                          "continuations_if_publicly_eligible": ["S", "A"]}
                         for task in CASES],
            "per_root_maximum_usd": PER_ROOT_USD,
            "maximum_authorised_usd": MAXIMUM_USD,
            "assessment_allowance_usd": ASSESSMENT_USD,
            "worker_policy": "B0 three-cell ladder, same task ceiling in S and A",
            "controller_profile": "standard", "controller_invocations_per_A": 1,
            "eligibility": "settled producer charge and public failure or concrete report partial",
            "stop_rule": "stop on uncertain accounting, source mismatch, replay or unqualified identity",
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "host": controller_campaign_manifest.host_record(),
            "credential_method": "claude-code-wsl-subscription"}
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def validate(manifest: dict) -> None:
    if manifest != freeze():
        raise FeasibilityStop("feasibility manifest or host/source package changed")


def gate(manifest: dict, notice: dict) -> None:
    validate(manifest)
    if (notice.get("approved") is not True
            or notice.get("manifest_sha256") != manifest["manifest_sha256"]
            or notice.get("maximum_usd") != MAXIMUM_USD
            or notice.get("scope") != SCOPE
            or not isinstance(notice.get("date"), str)):
        raise FeasibilityStop("dated cost notice does not authorise this manifest")


def actor_path(manifest: dict, task_id: str, arm: str) -> Path:
    return SEEDS / (f"x5-recovery-{manifest['manifest_sha256'][:12]}-"
                    f"{task_id.lower()}-{arm.lower()}")


def root_id(manifest: dict, task_id: str, arm: str) -> str:
    return controller_evaluation.digest(
        {"manifest": manifest["manifest_sha256"], "task": task_id, "arm": arm})[:24]


def actor_package(manifest: dict, task_id: str, arm: str) -> dict:
    if arm == "B0":
        return manifest["packages"][task_id]
    snapshot = load(RUN_DIR / f"{task_id}-pair" / "snapshot.json")
    if snapshot.get("task_id") != task_id:
        raise FeasibilityStop("successor snapshot has the wrong task")
    return {"actor_files": snapshot["actor_sha256"]}


def verify_initial_actor(manifest: dict, task_id: str, arm: str) -> None:
    """Bind every worker-visible file, including editable files, at dispatch."""
    actor = actor_path(manifest, task_id, arm)
    expected = actor_package(manifest, task_id, arm)["actor_files"]
    if set(expected) != protocol.PUBLIC_FILES[task_id]:
        raise FeasibilityStop("actor snapshot file set changed")
    for name, value in expected.items():
        path = actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != value:
            raise FeasibilityStop(f"actor changed before dispatch: {task_id}/{arm}/{name}")


def executor(manifest: dict, task_id: str, arm: str) -> task_executor.TaskExecutor:
    actor = actor_path(manifest, task_id, arm)
    task = {"actor_files": actor_package(manifest, task_id, arm)["actor_files"],
            "editable_paths": load(actor / "acceptance.json")["editable_paths"]}
    return task_executor.TaskExecutor(
        actor, screen.controller_x5_worker_adapter.X5WslAdapter(task),
        command_runner=isolated_public_runner(task),
        campaign_prompt=None if arm == "B0" else PROMPT)


def admit(manifest: dict, task_id: str, arm: str) -> None:
    actor = actor_path(manifest, task_id, arm)
    package_value = actor_package(manifest, task_id, arm)
    contract = screen._contract(actor, package_value)
    editable = load(actor / "acceptance.json")["editable_paths"]
    protected = sorted(set(package_value["actor_files"]) - set(editable))
    rid = root_id(manifest, task_id, arm)
    executor(manifest, task_id, arm).admit(
        goal=(actor / "issue.md").read_text(encoding="utf-8"),
        scope=editable, permissions=["read", "edit"], input_paths=protected,
        acceptance_path=contract, budget_usd=PER_ROOT_USD,
        authority_id=controller_evaluation.digest({"root": rid, "grant": "x5-recovery"})[:32],
        actor="x5-recovery-feasibility", root_id=rid,
        task_id=f"{task_id.lower()}-{arm.lower()}")


def prepare(manifest: dict) -> dict:
    validate(manifest)
    CredentialStore().inspect()
    if RUN_DIR.exists() or RUN_DIR.is_symlink():
        raise FeasibilityStop("single-use feasibility run already exists")
    for task_id in CASES:
        preview = Path(tempfile.mkdtemp(prefix="x5-recovery-host-", dir=SEEDS))
        try:
            for name, expected in manifest["packages"][task_id]["actor_files"].items():
                data = (source(task_id) / name).read_bytes()
                if sha(data) != expected:
                    raise FeasibilityStop("frozen preflight source changed")
                (preview / name).write_bytes(data)
            config = preview / ".mcp.json"
            config.write_bytes(MCP.read_bytes())
            config.chmod(0o600)
            graph = subprocess.run([str(NODE), str(GRAFT), "build", str(preview)],
                                   cwd=preview, capture_output=True, text=True,
                                   timeout=120, check=False)
            if graph.returncode or not (preview / "graft").is_dir():
                raise FeasibilityStop("provider-free Controller host preflight failed: "
                                      + graph.stderr[-300:])
            with hidden_evaluation_tree(ROOT):
                controller_dispatch.ControllerRuntimeAdapter().capability(preview)
        finally:
            if preview.resolve().parent != SEEDS.resolve():
                raise FeasibilityStop("preflight cleanup path escaped seed root")
            shutil.rmtree(preview)
    RUN_DIR.mkdir(parents=True)
    for task_id in CASES:
        actor = actor_path(manifest, task_id, "B0")
        if actor.exists() or actor.is_symlink():
            raise FeasibilityStop("producer actor path was already used")
        actor.mkdir(mode=0o700)
        for name, expected in manifest["packages"][task_id]["actor_files"].items():
            data = (source(task_id) / name).read_bytes()
            if sha(data) != expected:
                raise FeasibilityStop("frozen source actor changed")
            (actor / name).write_bytes(data)
        admit(manifest, task_id, "B0")
    exclusive(RUN_DIR / "prepared.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "producer_roots": {task: root_id(manifest, task, "B0") for task in CASES},
               "provider_calls": 0})
    return {"prepared_producers": len(CASES), "provider_calls": 0}


def require_ready(manifest: dict, task_id: str, arm: str) -> task_executor.TaskExecutor:
    entry = executor(manifest, task_id, arm)
    status = entry.status(root_id(manifest, task_id, arm))
    if (status["state"] != "ready" or status["budget"]["spent_usd"] != 0
            or status["budget"]["unresolved"]
            or status["budget"]["limit_usd"] != PER_ROOT_USD):
        raise FeasibilityStop("single-use task root is not ready")
    return entry


def prepare_successors(manifest: dict, task_id: str, producer_state: dict) -> dict:
    original = actor_path(manifest, task_id, "B0")
    task = {"actor_files": manifest["packages"][task_id]["actor_files"],
            "editable_paths": load(original / "acceptance.json")["editable_paths"]}
    snapshot_dir = RUN_DIR / f"{task_id}-pair"
    record = protocol.twins(task_id, original, producer_state, snapshot_dir,
                            isolated_public_runner(task))
    for arm in ("S", "A"):
        actor = actor_path(manifest, task_id, arm)
        if actor.exists() or actor.is_symlink():
            raise FeasibilityStop("successor actor path was already used")
        actor.mkdir(mode=0o700)
        for name, expected in record["actor_sha256"].items():
            data = (snapshot_dir / arm / name).read_bytes()
            if sha(data) != expected:
                raise FeasibilityStop("twin public snapshot changed")
            (actor / name).write_bytes(data)
        if arm == "A":
            config = actor / ".mcp.json"
            config.write_bytes(MCP.read_bytes())
            config.chmod(0o600)
            graph = subprocess.run([str(NODE), str(GRAFT), "build", str(actor)],
                                   cwd=actor, capture_output=True, text=True,
                                   timeout=120, check=False)
            if graph.returncode or not (actor / "graft").is_dir():
                raise FeasibilityStop("successor Controller Graft build failed: "
                                      + graph.stderr[-300:])
            controller_dispatch.ControllerRuntimeAdapter().capability(actor)
        admit(manifest, task_id, arm)
    return record


def producer(manifest: dict, notice: dict, task_id: str) -> dict:
    gate(manifest, notice)
    if task_id not in CASES or load(RUN_DIR / "prepared.json")["manifest_sha256"] != manifest["manifest_sha256"]:
        raise FeasibilityStop("producer is outside prepared manifest")
    case_index = CASES.index(task_id)
    if case_index > 0:
        previous = CASES[case_index - 1]
        first = load(RUN_DIR / f"{previous}-producer-result.json")
        if first.get("qualified") is not True:
            raise FeasibilityStop("previous producer did not settle safely")
        if first.get("eligible") and not (
                load(RUN_DIR / f"{previous}-S-result.json").get("qualified") is True
                and load(RUN_DIR / f"{previous}-A-result.json").get("qualified") is True):
            raise FeasibilityStop("previous matched case has not settled")
    entry = require_ready(manifest, task_id, "B0")
    verify_initial_actor(manifest, task_id, "B0")
    CredentialStore().inspect()
    exclusive(RUN_DIR / f"{task_id}-producer-started.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "root_id": root_id(manifest, task_id, "B0")})
    start = time.monotonic()
    state = entry.run(root_id(manifest, task_id, "B0"))
    eligible = False
    snapshot = None
    error = None
    try:
        snapshot = prepare_successors(manifest, task_id, state)
        eligible = True
    except protocol.RecoveryStop as exc:
        error = str(exc)
    grade = None
    if not state["budget"]["unresolved"]:
        grade = controller_x5_recovery_grade.grade(
            actor_path(manifest, task_id, "B0"), oracle(task_id))
    qualified = (grade is not None and (eligible or error == "no publicly observable unresolved work"))
    result = {"manifest_sha256": manifest["manifest_sha256"],
              "task_id": task_id, "root_id": root_id(manifest, task_id, "B0"),
              "state": state["state"], "budget": state["budget"],
              "attempt_count": len(state["attempts"]), "eligible": eligible,
              "qualified": qualified,
              "public_stop_reason": error, "snapshot": snapshot,
              "protected_grade_after_eligibility": grade,
              "elapsed_s": round(time.monotonic() - start, 3)}
    exclusive(RUN_DIR / f"{task_id}-producer-result.json", result)
    return {"task_id": task_id, "eligible": eligible, "qualified": qualified,
            "spent_usd": state["budget"]["spent_usd"], "state": state["state"]}


def assessment_inputs(actor: Path, task_id: str) -> dict:
    editable = load(actor / "acceptance.json")["editable_paths"]
    issue_lines = [line for line in (actor / "issue.md").read_text(encoding="utf-8").splitlines()
                   if line.strip()]
    if not issue_lines:
        raise FeasibilityStop("public issue has no citation")
    assertions = [line for line in (actor / "public_check.py").read_text(
        encoding="utf-8").splitlines() if line.lstrip().startswith("assert ")]
    if not assertions or len(set(issue_lines)) != len(issue_lines) or len(set(assertions)) != len(assertions):
        raise FeasibilityStop("public check has no assertion citation")
    trace = (actor / "trace.json").read_text(encoding="utf-8").strip()
    quotes = ([{"source": "issue.md", "quote": line} for line in issue_lines]
              + [{"source": "public_check.py", "quote": line} for line in assertions]
              + [{"source": "trace.json", "quote": trace}])
    if len(quotes) > controller_public_assessment.MAX_CITATIONS:
        raise FeasibilityStop("public citations exceed the packet limit")
    sources = sorted(protocol.PUBLIC_FILES[task_id] - {"acceptance.json"})
    return {"issue": "issue.md", "source_paths": sources,
            "quote_requests": quotes,
            "operational": {"context_tokens": 1000, "deadline_seconds": None,
                            "prior_local_repairs": 1, "required_artefacts": editable,
                            "deadline": None, "authorised_task_budget_usd": PER_ROOT_USD,
                            "observed_at": "2026-09-29T00:00:00Z"}}


def actionable_handoff(dispatch: dict | None, task_id: str) -> bool:
    """Require a code-cited finding and a concrete next check before expansion."""
    handoff = dispatch.get("worker_handoff") if isinstance(dispatch, dict) else None
    if not isinstance(handoff, dict) or handoff.get("controller_used") is not True:
        return False
    editable_code = protocol.PUBLIC_FILES[task_id] - {
        "report.json", "acceptance.json", "app.py", "issue.md", "trace.json", "public_check.py"}
    findings = handoff.get("verified_findings")
    if not isinstance(findings, list) or not any(
            isinstance(row, dict) and isinstance(row.get("source"), str)
            and isinstance(row.get("text"), str) and row["text"].strip()
            and any(name in row["source"] for name in editable_code)
            for row in findings):
        return False
    action = handoff.get("safe_next_action")
    return (isinstance(action, str) and len(action.strip()) >= 25
            and "restore the frozen acceptance criteria" not in action.lower()
            and any(name in action for name in editable_code | {"public_check.py"}))


def continuation(manifest: dict, notice: dict, task_id: str, arm: str) -> dict:
    gate(manifest, notice)
    if task_id not in CASES or arm not in {"S", "A"}:
        raise FeasibilityStop("unknown continuation")
    producer_result = load(RUN_DIR / f"{task_id}-producer-result.json")
    if (producer_result.get("manifest_sha256") != manifest["manifest_sha256"]
            or producer_result.get("qualified") is not True
            or producer_result.get("eligible") is not True
            or producer_result.get("snapshot") != load(RUN_DIR / f"{task_id}-pair/snapshot.json")):
        raise FeasibilityStop("producer eligibility or frozen snapshot changed")
    if arm == "A" and load(RUN_DIR / f"{task_id}-S-result.json").get("qualified") is not True:
        raise FeasibilityStop("matched S arm must settle first")
    entry = require_ready(manifest, task_id, arm)
    verify_initial_actor(manifest, task_id, arm)
    actor = actor_path(manifest, task_id, arm)
    store = CredentialStore()
    store.inspect()
    if arm == "A":
        controller_dispatch.ControllerRuntimeAdapter().capability(actor)
    exclusive(RUN_DIR / f"{task_id}-{arm}-started.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "root_id": root_id(manifest, task_id, arm)})
    start = time.monotonic()
    session_name = None
    session_open = False
    environment = dict(os.environ)
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
            worker = entry.adapter
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
            entry.run(root_id(manifest, task_id, arm))
        else:
            inputs = assessment_inputs(actor, task_id)
            snapshot = load(RUN_DIR / f"{task_id}-pair/snapshot.json")
            interpreter = WslPublicInterpreter(
                distro="kali-linux", linux_user="wsl", claude_path=screen.CLAUDE,
                launcher_path=str(ROOT / "tools/controller_wsl_launch.py"),
                allowance_usd=ASSESSMENT_USD, runner=screen._local_runner)
            with hidden_evaluation_tree(ROOT):
                workflow = controller_workflow.execute(
                    entry, root_id(manifest, task_id, arm),
                    interpreter=interpreter, assessment_allowance_usd=ASSESSMENT_USD,
                    controller_adapter=controller_dispatch.ControllerRuntimeAdapter(),
                    explicit_mode="on",
                    public_passed=snapshot["public_check_exit_code"] == 0, **inputs)
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
    state = entry.status(root_id(manifest, task_id, arm))
    grade = None
    if not state["budget"]["unresolved"] and not session_open:
        try:
            grade = controller_x5_recovery_grade.grade(actor, oracle(task_id))
        except Exception as exc:
            error = (error + "; " if error else "") + "protected grade: " + str(exc)[:250]
    decision = (state.get("routing_decision") or {}).get("decision") or {}
    dispatch = workflow.get("dispatch") if workflow else None
    actionable = actionable_handoff(dispatch, task_id) if arm == "A" else None
    role_budget = None
    if dispatch and dispatch.get("controller_result"):
        role_dir = Path(dispatch["controller_result"].get("controller_run_dir", ""))
        if role_dir.is_relative_to(actor) and (role_dir / "dispatch-budget.json").is_file():
            role_budget = dispatch_budget.DispatchBudget(
                role_dir / "dispatch-budget.json").snapshot()
    identities_valid = all(
        (attempt.get("receipt") or {}).get("identity_valid") is True
        and bool((attempt.get("receipt") or {}).get("actual_model"))
        for attempt in state["attempts"])
    qualified = (error is None and grade is not None and identities_valid
                 and bool(state["attempts"]) and state["state"] in protocol.TERMINAL
                 and not state["budget"]["unresolved"] and not state["budget"]["breached"]
                 and state["budget"]["spent_usd"] <= PER_ROOT_USD
                 and (arm == "S" or (
                     decision.get("effective_action") == "controller"
                     and dispatch is not None and dispatch.get("stage") == "worker-ready"
                     and dispatch.get("controller_invocations") == 1
                     and actionable is True
                     and role_budget is not None
                     and not role_budget["unresolved"] and not role_budget["breached"]
                     and all(((call.get("telemetry") or {}).get("identity") or {}).get(
                         "identity_valid") is True
                         for call in role_budget["invocations"].values()))))
    result = {"manifest_sha256": manifest["manifest_sha256"], "task_id": task_id,
              "arm": arm, "root_id": root_id(manifest, task_id, arm),
              "state": state["state"], "budget": state["budget"],
              "attempt_count": len(state["attempts"]), "grade": grade,
              "effective_action": decision.get("effective_action"),
              "controller_stage": dispatch.get("stage") if dispatch else None,
              "controller_invocations": dispatch.get("controller_invocations") if dispatch else 0,
              "controller_role_cost_usd": role_budget["spent_usd"] if role_budget else None,
              "controller_handoff_actionable": actionable,
              "worker_identity_valid": identities_valid, "qualified": qualified,
              "error": error, "credential_reconciled": not session_open,
              "elapsed_s": round(time.monotonic() - start, 3)}
    exclusive(RUN_DIR / f"{task_id}-{arm}-result.json", result)
    return {"task_id": task_id, "arm": arm, "state": state["state"],
            "quality": grade["quality"] if grade else None,
            "spent_usd": state["budget"]["spent_usd"],
            "qualified": qualified, "error": error}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "prepare", "producer", "continuation"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--notice", type=Path)
    parser.add_argument("--task", choices=CASES)
    parser.add_argument("--arm", choices=("S", "A"))
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() != 0:
        raise FeasibilityStop("feasibility runner requires attested WSL root")
    if args.mode == "freeze":
        exclusive(args.manifest, freeze())
        print(json.dumps({"manifest_sha256": load(args.manifest)["manifest_sha256"],
                          "provider_calls": 0}))
        return
    manifest = load(args.manifest)
    if args.mode == "prepare":
        print(json.dumps(prepare(manifest)))
        return
    if args.notice is None or args.task is None:
        raise FeasibilityStop("paid mode requires notice and task")
    notice = load(args.notice)
    if args.mode == "producer":
        print(json.dumps(producer(manifest, notice, args.task)))
        return
    if args.arm is None:
        raise FeasibilityStop("continuation requires an arm")
    print(json.dumps(continuation(manifest, notice, args.task, args.arm)))


if __name__ == "__main__":
    main()
