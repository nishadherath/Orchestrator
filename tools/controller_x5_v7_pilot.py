#!/usr/bin/env python3
"""Single-use X5 v7 development continuation on the attested WSL host.

Freeze and prepare are provider-free. Episode calls require a separate notice.
An interrupted episode retains its started marker and N1 root for reconciliation;
this driver never replays a provider invocation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path

import controller_campaign_manifest
import controller_dispatch
import controller_evaluation
import dispatch_budget
import controller_workflow
import controller_x5_v6_pilot as old
import controller_x5_v7_pilot_grade
import controller_x5_v6_screen as screen
import task_executor
from controller_wsl_interpreter import WslPublicInterpreter
from worker_wsl_auth import ACTOR_UID, CredentialStore, _credential, _fresh
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import GRAFT, MCP, NODE, isolated_public_runner

ROOT = Path(__file__).resolve().parents[1]
SCREEN_MANIFEST = ROOT / "test/results/2026-09-29-controller-x5-v6-screen-manifest.json"
SCREEN_RESULTS = ROOT / "test/results/2026-09-29-controller-x5-v6-screen-results.json"
SCREEN_ARCHIVE = Path("/var/lib/orchestrator-worker-n4/archives/x5-v6-screen-417570f779e2")
V6_MANIFEST = ROOT / "test/results/2026-09-29-controller-x5-v6-pilot-manifest.json"
V6_STOP = ROOT / "test/results/2026-09-29-controller-x5-v6-pilot-stop.json"
RUN_DIR = ROOT / "test/results/2026-09-29-controller-x5-v7-pilot-run"
EPISODE_BUDGET_USD = 5.0
MAXIMUM_USD = 60.0
ASSESSMENT_USD = 0.5
S_PROMPT = "Investigate the public incident, verify distinct causes and report truthful progress."
EXPECTED = screen.EXPECTED_ACTIONS


class PilotError(RuntimeError):
    """The paired pilot cannot safely advance."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return controller_evaluation.digest(value)


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise PilotError(f"missing or redirected file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    controller_dispatch._atomic_json(path, value)


def exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def schedule() -> list[dict]:
    return [{**row, "maximum_usd": EPISODE_BUDGET_USD}
            for row in old.schedule()[6:]]


def historical_evidence() -> dict:
    previous = load(V6_MANIFEST)
    stop = load(V6_STOP)
    if (previous.get("manifest_sha256") != digest({
            k: v for k, v in previous.items() if k != "manifest_sha256"})
            or stop.get("manifest_sha256") != previous["manifest_sha256"]
            or stop.get("status") != "stopped-after-six-for-measurement-contract-defect"
            or stop.get("completed_sequences") != list(range(1, 7))
            or stop.get("first_unstarted_sequence") != 7
            or (old.RUN_DIR / "007-started.json").exists()):
        raise PilotError("stopped v6 pilot evidence changed or was continued")
    actors = {}
    spent = 0.0
    for row in previous["episodes"][:6]:
        number = f"{row['sequence']:03d}"
        result_path = old.RUN_DIR / f"{number}-result.json"
        result = load(result_path)
        if (sha(result_path) != stop["result_sha256"][number]
                or result.get("status") != "completed"
                or result.get("budget_unresolved")
                or result.get("root_id") != old.root_id(previous, row)):
            raise PilotError(f"stopped v6 receipt changed: {number}")
        spent += result["budget_spent_usd"]
        actor = old.project(previous, row)
        editable = load(actor / "acceptance.json")["editable_paths"]
        if any((actor / name).is_symlink() or not (actor / name).is_file()
               for name in editable):
            raise PilotError(f"stopped v6 actor was redirected: {number}")
        actors[number] = {name: sha(actor / name) for name in sorted(editable)}
    if round(spent, 9) != stop["settled_cost_usd"]:
        raise PilotError("stopped v6 cost reconciliation changed")
    return {"v6_manifest_sha256": previous["manifest_sha256"],
            "v6_stop_sha256": sha(V6_STOP),
            "v6_result_sha256": stop["result_sha256"],
            "v6_actor_editable_sha256": actors}


def screen_evidence() -> tuple[dict, dict]:
    manifest = load(SCREEN_MANIFEST)
    result = load(SCREEN_RESULTS)
    if (manifest.get("manifest_sha256") != digest({
            k: v for k, v in manifest.items() if k != "manifest_sha256"})
            or result.get("manifest_sha256") != manifest["manifest_sha256"]
            or result.get("screen_status") != "passed-prospective-routing-gate"
            or result.get("provider_calls") != 6
            or result.get("budget_unresolved")
            or len(result.get("results", [])) != 6):
        raise PilotError("v6 screen is not a settled six-task gate")
    for task, row in zip(screen.TASKS, result["results"]):
        if (row.get("task_id") != task or row.get("assessment_status") != "settled"
                or row.get("decision_frozen") is not True
                or row.get("effective_action") != EXPECTED[task]
                or row.get("budget_unresolved")):
            raise PilotError(f"screen gate result changed: {task}")
    controller_campaign_manifest.verify_package(
        SCREEN_ARCHIVE, manifest["runtime_package"], require_materialised=True)
    if manifest["packages"] != screen._packages(screen._rows()):
        raise PilotError("screen actor or protected oracle package drift")
    return manifest, result


def freeze() -> dict:
    screen_manifest, _ = screen_evidence()
    body = {"schema_version": 1, "stage": "controller-x5-v7-development-continuation",
            "screen_manifest_sha256": screen_manifest["manifest_sha256"],
            "screen_results_sha256": sha(SCREEN_RESULTS),
            "historical_evidence": historical_evidence(),
            "packages": screen_manifest["packages"],
            "episodes": schedule(), "maximum_authorised_usd": MAXIMUM_USD,
            "assessment_allowance_usd": ASSESSMENT_USD,
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "host": controller_campaign_manifest.host_record(),
            "credential_method": "claude-code-wsl-subscription",
            "stop_rule": "stop on failed required admission, unqualified host or unresolved charge",
            "quality_rule": "host functional acceptance plus M/E/D/N/H 40/25/15/10/10 with critical veto"}
    body["manifest_sha256"] = digest(body)
    return body


def validate(manifest: dict) -> None:
    if (manifest.get("manifest_sha256") != digest({
            k: v for k, v in manifest.items() if k != "manifest_sha256"})
            or manifest.get("schema_version") != 1
            or manifest.get("stage") != "controller-x5-v7-development-continuation"
            or manifest.get("episodes") != schedule()
            or manifest.get("maximum_authorised_usd") != MAXIMUM_USD
            or manifest.get("assessment_allowance_usd") != ASSESSMENT_USD
            or manifest.get("credential_method") != "claude-code-wsl-subscription"
            or manifest.get("stop_rule") !=
            "stop on failed required admission, unqualified host or unresolved charge"
            or manifest.get("quality_rule") !=
            "host functional acceptance plus M/E/D/N/H 40/25/15/10/10 with critical veto"
            or manifest.get("historical_evidence") != historical_evidence()):
        raise PilotError("pilot manifest contract is invalid")
    controller_campaign_manifest.verify_package(
        ROOT, manifest["runtime_package"], require_materialised=False)
    if manifest["host"] != controller_campaign_manifest.host_record():
        raise PilotError("pilot host identity or relevant settings changed")
    screen_manifest, _ = screen_evidence()
    if (manifest["screen_manifest_sha256"] != screen_manifest["manifest_sha256"]
            or manifest["screen_results_sha256"] != sha(SCREEN_RESULTS)
            or manifest["packages"] != screen_manifest["packages"]):
        raise PilotError("pilot no longer binds the qualified v6 screen")


def project(manifest: dict, row: dict) -> Path:
    return SEEDS / (f"x5-v7-pilot-{manifest['manifest_sha256'][:12]}-"
                    f"{row['sequence']:03d}-{row['task_id'].lower()}-{row['arm'].lower()}")


def root_id(manifest: dict, row: dict) -> str:
    return digest({"pilot": manifest["manifest_sha256"],
                   "episode": row["sequence"]})[:24]


def executor(manifest: dict, row: dict) -> task_executor.TaskExecutor:
    actor = project(manifest, row)
    editable = load(actor / "acceptance.json")["editable_paths"]
    package = manifest["packages"][row["task_id"]]
    task = {"actor_files": package["actor_files"], "editable_paths": editable}
    return task_executor.TaskExecutor(
        actor, screen.controller_x5_worker_adapter.X5WslAdapter(task),
        command_runner=isolated_public_runner(task),
        campaign_prompt=None if row["arm"] == "B" else S_PROMPT)


def prepare(manifest: dict) -> dict:
    validate(manifest)
    CredentialStore().inspect()
    if RUN_DIR.exists() or RUN_DIR.is_symlink():
        raise PilotError("pilot run directory already exists; inspect before preparing again")
    RUN_DIR.mkdir(parents=True)
    prepared = []
    for row in manifest["episodes"]:
        task = row["task_id"]
        package = manifest["packages"][task]
        actor = project(manifest, row)
        if actor.exists() or actor.is_symlink():
            raise PilotError(f"single-use pilot actor already exists: {row['sequence']}")
        source = (screen._case_roots(task, screen.CASE_DIRS[task])[0]
                  if task in screen.CASE_DIRS else
                  ROOT / "test/fixtures/controller_x3/development" / task / "actor")
        actor.mkdir(mode=0o700)
        for relative, expected in package["actor_files"].items():
            data = (source / relative).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise PilotError(f"actor package changed: {task}/{relative}")
            target = actor / relative
            target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            target.write_bytes(data)
        if row["arm"] == "A":
            config = actor / ".mcp.json"
            config.write_bytes(MCP.read_bytes())
            config.chmod(0o600)
            graph = subprocess.run([str(NODE), str(GRAFT), "build", str(actor)],
                                   cwd=actor, capture_output=True, text=True,
                                   timeout=120, check=False)
            if graph.returncode or not (actor / "graft").is_dir():
                raise PilotError(f"Controller actor Graft build failed: {task}: "
                                 + graph.stderr[-300:])
            controller_dispatch.ControllerRuntimeAdapter().capability(actor)
        contract = screen._contract(actor, package)
        editable = load(actor / "acceptance.json")["editable_paths"]
        protected = sorted(set(package["actor_files"]) - set(editable))
        entry = executor(manifest, row)
        spec = (None if row["arm"] == "B" else
                {"schema_version": 3, "arm": "candidate",
                 "manifest_sha256": manifest["manifest_sha256"],
                 "cost_ceiling_usd": EPISODE_BUDGET_USD,
                 "repair_cells": ["worker-sonnet-low", "worker-opus-high"]})
        rid = root_id(manifest, row)
        entry.admit(goal=(actor / "issue.md").read_text(encoding="utf-8"),
                    scope=editable, permissions=["read", "edit"],
                    input_paths=protected, acceptance_path=contract,
                    budget_usd=EPISODE_BUDGET_USD,
                    authority_id=digest({"pilot": rid, "grant": "x5-v7"})[:32],
                    actor="x5-v7-pilot", root_id=rid,
                    task_id=f"{task.lower()}-{row['arm'].lower()}",
                    experimental_dispatch=spec)
        prepared.append({"sequence": row["sequence"], "task_id": task,
                         "arm": row["arm"], "root_id": rid, "project": str(actor)})
    value = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "status": "prepared-no-provider-call", "provider_calls": 0,
             "episodes": prepared}
    atomic(RUN_DIR / "prepared.json", value)
    return {"prepared": len(prepared), "provider_calls": 0}


def settle_session(store: CredentialStore, name: str) -> None:
    token = store.sessions / name / ".credentials.json"
    info = token.lstat()
    if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_uid not in (0, ACTOR_UID)):
        raise PilotError("Controller credential copy needs manual reconciliation")
    _fresh(_credential(token, info.st_uid))
    if info.st_uid == 0:
        os.chown(token, ACTOR_UID, ACTOR_UID)
    store.finish(name)


def gate(manifest: dict, row: dict, notice: dict) -> None:
    if (notice.get("authorised_under_threshold") is not True
            or notice.get("manifest_sha256") != manifest["manifest_sha256"]
            or notice.get("maximum_pilot_usd") != MAXIMUM_USD
            or notice.get("scope") != "12 paired X5 v7 development continuation episodes"):
        raise PilotError("v7 dated cost notice does not match manifest")
    prepared = load(RUN_DIR / "prepared.json")
    if (prepared.get("manifest_sha256") != manifest["manifest_sha256"]
            or prepared.get("status") != "prepared-no-provider-call"
            or len(prepared.get("episodes", [])) != 12):
        raise PilotError("pilot roots are not fully prepared")
    for spec, actual in zip(manifest["episodes"], prepared["episodes"]):
        if actual != {"sequence": spec["sequence"], "task_id": spec["task_id"],
                      "arm": spec["arm"], "root_id": root_id(manifest, spec),
                      "project": str(project(manifest, spec))}:
            raise PilotError("prepared pilot root differs from frozen schedule")
    index = next(i for i, spec in enumerate(manifest["episodes"])
                 if spec["sequence"] == row["sequence"])
    for prior in manifest["episodes"][:index]:
        result = load(RUN_DIR / f"{prior['sequence']:03d}-result.json")
        prior_root = root_id(manifest, prior)
        state = executor(manifest, prior).status(prior_root)
        if (result.get("status") != "completed"
                or result.get("budget_unresolved")
                or result.get("manifest_sha256") != manifest["manifest_sha256"]
                or result.get("root_id") != prior_root
                or result.get("budget_spent_usd") != state["budget"]["spent_usd"]
                or result.get("budget_spent_usd", 1e9) > prior["maximum_usd"]
                or state["budget"]["breached"]
                or state["budget"]["unresolved"]
                or result.get("required_admission_met") is not True):
            raise PilotError(f"pilot stopped or root changed after episode {prior['sequence']}")
    if ((RUN_DIR / f"{row['sequence']:03d}-started.json").exists()
            or (RUN_DIR / f"{row['sequence']:03d}-result.json").exists()):
        raise PilotError("single-use pilot episode was already started")


def episode(manifest: dict, notice: dict, sequence: int) -> dict:
    validate(manifest)
    if sequence not in range(7, 19):
        raise PilotError("episode sequence is outside the frozen pilot")
    row = manifest["episodes"][sequence - 7]
    gate(manifest, row, notice)
    actor = project(manifest, row)
    entry = executor(manifest, row)
    rid = root_id(manifest, row)
    initial = entry.status(rid)
    if (initial["state"] != "ready" or initial["budget"]["spent_usd"] != 0
            or initial["budget"]["unresolved"]
            or initial["budget"]["limit_usd"] != row["maximum_usd"]):
        raise PilotError("prepared N1 root is no longer ready")
    store = CredentialStore()
    store.inspect()
    if row["arm"] == "A":
        controller_dispatch.ControllerRuntimeAdapter().capability(actor)
    exclusive(RUN_DIR / f"{sequence:03d}-started.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "sequence": sequence, "root_id": rid, "project": str(actor)})
    start = time.monotonic()
    session_name = None
    session_open = False
    original_env = dict(os.environ)
    workflow = None
    error = None
    try:
        if row["arm"] == "A":
            session_name = "inv-" + uuid.uuid4().hex
            session = store.begin(session_name)
            clean = {k: v for k, v in os.environ.items()
                     if k not in {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
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
                    settle_session(store, session_name)
                    session_open = False
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
                try:
                    return original_run(request)
                finally:
                    os.environ["CLAUDE_CONFIG_DIR"] = str(session)

            worker.run = run_worker
        elif row["arm"] not in {"B", "S"}:
            raise PilotError("episode has an unknown arm")
        editable = load(actor / "acceptance.json")["editable_paths"]
        inputs = screen._inputs(actor, editable)
        interpreter = WslPublicInterpreter(
            distro="kali-linux", linux_user="wsl", claude_path=screen.CLAUDE,
            launcher_path=str(ROOT / "tools/controller_wsl_launch.py"),
            allowance_usd=ASSESSMENT_USD, runner=screen._local_runner)
        if row["arm"] == "B":
            state = entry.run(rid)
        elif row["arm"] == "S":
            entry.assess_public(rid, interpreter=interpreter, **inputs)
            entry.freeze_public_selection(rid)
            state = entry.run(rid)
        else:
            workflow = controller_workflow.execute(
                entry, rid, issue=inputs["issue"],
                source_paths=inputs["source_paths"],
                quote_requests=inputs["quote_requests"],
                interpreter=interpreter, operational=inputs["operational"],
                assessment_allowance_usd=ASSESSMENT_USD,
                controller_adapter=controller_dispatch.ControllerRuntimeAdapter(),
                controller_profile=(row["controller_profile"] if
                                    row["controller_profile"] == "frontier-candidate"
                                    else None),
                explicit_experimental_profile=(
                    row["controller_profile"] == "frontier-candidate"))
            state = workflow["task"]
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:500]
    finally:
        if session_open:
            try:
                settle_session(store, session_name)
                session_open = False
            except Exception as exc:
                error = (error + "; " if error else "") + (
                    "credential reconciliation required: " + str(exc)[:350])
        os.environ.clear()
        os.environ.update(original_env)

    state = entry.status(rid)
    budget = state["budget"]
    routing = state.get("routing_decision") or {}
    decision = routing.get("decision") or {}
    dispatch = workflow.get("dispatch") if isinstance(workflow, dict) else None
    controller_result = dispatch.get("controller_result") if dispatch else None
    controller_run_dir = (controller_result or {}).get("controller_run_dir")
    role_budget = None
    if controller_run_dir:
        role_dir = Path(controller_run_dir)
        if role_dir.is_relative_to(actor) and (role_dir / "dispatch-budget.json").is_file():
            role_budget = dispatch_budget.DispatchBudget(
                role_dir / "dispatch-budget.json").snapshot()
    action = decision.get("effective_action") if row["arm"] == "A" else None
    required = (row["arm"] != "A" or (action == EXPECTED[row["task_id"]]
                and (action != "controller" or
                     dispatch is not None and dispatch.get("stage") == "worker-ready")))
    settled = (not budget["unresolved"] and not budget["breached"]
               and budget["spent_usd"] <= row["maximum_usd"]
               and state["state"] != "uncertain")
    if budget["breached"] or budget["spent_usd"] > row["maximum_usd"]:
        error = (error + "; " if error else "") + "episode budget ceiling breached"
    grade = None
    if settled and session_open is False:
        try:
            grade = controller_x5_v7_pilot_grade.grade(row["task_id"], actor,
                                                        manifest)
        except Exception as exc:
            error = (error + "; " if error else "") + (
                "protected grading failed: " + type(exc).__name__ + ": "
                + str(exc)[:350])
    if dispatch and dispatch.get("controller_invocations") and role_budget is None:
        error = (error + "; " if error else "") + "Controller role budget is absent"
    if role_budget and (role_budget["unresolved"] or role_budget["breached"]):
        error = (error + "; " if error else "") + "Controller role budget is unresolved or breached"
    if role_budget and any(
            ((call.get("telemetry") or {}).get("identity") or {}).get("identity_valid") is False
            for call in role_budget["invocations"].values()):
        error = (error + "; " if error else "") + "Controller role identity failed"
    attempts = []
    for attempt in state["attempts"]:
        receipt = attempt.get("receipt") or {}
        if receipt and (receipt.get("identity_valid") is not True
                        or not receipt.get("actual_model")):
            error = (error + "; " if error else "") + "worker identity is unqualified"
        attempts.append({"requested_cell": attempt.get("requested_cell"),
                         "process_state": attempt.get("process_state"),
                         "status": receipt.get("status"),
                         "actual_model": receipt.get("actual_model"),
                         "identity_valid": receipt.get("identity_valid"),
                         "requested_effort": receipt.get("requested_effort"),
                         "served_effort": receipt.get("served_effort"),
                         "cost_usd": receipt.get("cost_usd"),
                         "wall_clock_s": receipt.get("wall_clock_s")})
    status = "completed" if error is None and required and settled and grade else "stopped"
    assessment = state.get("public_assessment") or {}
    assessment_cost = (assessment.get("result") or {}).get("telemetry", {}).get("cost_usd")
    result = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
              "sequence": sequence, "task_id": row["task_id"], "arm": row["arm"],
              "status": status, "error": error, "root_id": rid,
              "project": str(actor), "elapsed_s": round(time.monotonic() - start, 3),
              "effective_action": action,
              "controller_profile": row["controller_profile"] if row["arm"] == "A" else None,
              "controller_stage": dispatch.get("stage") if dispatch else None,
              "worker_attempt_count": len(state["attempts"]),
              "worker_attempts": attempts,
              "assessment_cost_usd": assessment_cost,
              "controller_invocations": dispatch.get("controller_invocations") if dispatch else 0,
              "controller_run_dir": controller_run_dir,
              "controller_role_call_count": (len(role_budget["invocations"])
                                             if role_budget else None),
              "controller_role_cost_usd": role_budget["spent_usd"] if role_budget else None,
              "budget_spent_usd": budget["spent_usd"],
              "budget_unresolved": budget["unresolved"],
              "task_state": state["state"], "grade": grade,
              "required_admission_met": required,
              "credential_reconciled": not session_open}
    atomic(RUN_DIR / f"{sequence:03d}-result.json", result)
    return {key: result[key] for key in (
        "sequence", "task_id", "arm", "status", "error", "elapsed_s",
        "effective_action", "controller_stage", "worker_attempt_count",
        "budget_spent_usd", "budget_unresolved", "required_admission_met")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "prepare", "episode"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--notice", type=Path)
    parser.add_argument("--sequence", type=int)
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() != 0:
        raise PilotError("X5 pilot requires the attested WSL root host")
    if args.mode == "freeze":
        if args.manifest.exists() or args.manifest.is_symlink():
            raise PilotError("pilot manifest path already exists")
        value = freeze()
        args.manifest.write_text(json.dumps(value, indent=2, sort_keys=True)
                                 + "\n", encoding="utf-8")
        print(json.dumps({"manifest_sha256": value["manifest_sha256"],
                          "episodes": len(value["episodes"]),
                          "maximum_authorised_usd": MAXIMUM_USD}))
        return 0
    manifest = load(args.manifest)
    if args.mode == "prepare":
        print(json.dumps(prepare(manifest), sort_keys=True))
        return 0
    if args.notice is None or args.sequence is None:
        raise PilotError("episode needs --notice and --sequence")
    print(json.dumps(episode(manifest, load(args.notice), args.sequence),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
