#!/usr/bin/env python3
"""One bounded WSL Claude.ai Controller-to-worker integration attempt.

Run only after the dated X4 spend notice. The preflight root and credential
session are single-use. A failure leaves durable N1/controller records for
reconciliation; this script never retries an admitted provider invocation.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path("/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator")
sys.path.insert(0, str(ROOT / "tools"))

import controller_dispatch  # noqa: E402
import controller_workflow  # noqa: E402
import system_controller  # noqa: E402
import worker_wsl_auth  # noqa: E402
from controller_wsl_interpreter import WslPublicInterpreter  # noqa: E402
from task_executor import TaskExecutor  # noqa: E402
from worker_wsl_q3_adapter import Q3WslAdapter, isolated_public_runner  # noqa: E402

CLAUDE = "/opt/orchestrator-worker-runtime/bin/claude"
PREPARED = ROOT / "test/results/2026-09-28-controller-x4-wsl-preflight-v4.json"
OUT = ROOT / "test/results/2026-09-28-controller-x4-wsl-live-smoke-v4.json"
LAUNCHER = str(ROOT / "tools/controller_wsl_launch.py")


def settle_session(store: worker_wsl_auth.CredentialStore, name: str) -> None:
    """Commit a stopped Controller's credential refresh before worker launch."""
    token = store.sessions / name / ".credentials.json"
    info = token.lstat()
    if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_uid not in (0, worker_wsl_auth.ACTOR_UID)):
        raise RuntimeError("Controller credential copy needs manual reconciliation")
    data = worker_wsl_auth._credential(token, info.st_uid)
    worker_wsl_auth._fresh(data)
    if info.st_uid == 0:
        os.chown(token, worker_wsl_auth.ACTOR_UID, worker_wsl_auth.ACTOR_UID)
    store.finish(name)


def main() -> int:
    if os.geteuid() != 0 or OUT.exists():
        raise RuntimeError("root identity and fresh result path are required")
    prepared = json.loads(PREPARED.read_text(encoding="utf-8"))
    if (prepared.get("status") != "READY_NO_PROVIDER_CALL"
            or prepared.get("provider_calls") != 0):
        raise RuntimeError("X4 preflight is absent or not provider-free")
    project = Path(prepared["seed"])
    task = {"actor_files": prepared["actor_files"],
            "editable_paths": prepared["editable_paths"]}
    store = worker_wsl_auth.CredentialStore()
    store.inspect()
    worker = Q3WslAdapter(task)
    worker.capability(project)
    executor = TaskExecutor(project, worker,
                            command_runner=isolated_public_runner(task))
    root_id = prepared["root_id"]
    if executor.status(root_id)["state"] != "ready":
        raise RuntimeError("prepared N1 root is no longer ready")

    name = "inv-" + uuid.uuid4().hex
    session = store.begin(name)
    clean_env = {key: value for key, value in os.environ.items()
                 if key not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                                "CLAUDE_CODE_OAUTH_TOKEN", "WSLENV")}
    clean_env["CLAUDE_CONFIG_DIR"] = str(session)
    clean_env["PATH"] = "/opt/orchestrator-worker-runtime/bin:" + clean_env.get("PATH", "")
    os.environ.clear()
    os.environ.update(clean_env)
    session_open = True

    def local_wsl_runner(argv, **kwargs):
        prefix = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
                  "/usr/bin/env", "-C", "/tmp"]
        if argv[:len(prefix)] != prefix:
            raise RuntimeError("public interpreter host command changed")
        kwargs["env"] = clean_env
        return subprocess.run(argv[len(prefix):], cwd="/tmp", **kwargs)

    # The Controller uses the production role runner's restricted flags and
    # identity checks. Its factory is explicit because live root integration
    # is still experimental; this does not promote a default consumer path.
    controller = controller_dispatch.ControllerRuntimeAdapter(
        runner_factory=lambda path: lambda remaining: system_controller.LiveRoleRunner(
            path, remaining, permission_args=(),
            extra_args=controller_dispatch.CONTROL_ARGS,
            stream_json=True, require_identity=True, role_profile="standard"))
    interpreter = WslPublicInterpreter(
        distro="kali-linux", linux_user="root", claude_path=CLAUDE,
        allowance_usd=0.5, timeout_s=300, launcher_path=LAUNCHER,
        runner=local_wsl_runner)
    result = None
    error = None
    try:
        # The worker launcher manages its own private Claude.ai copy. Release
        # the Controller copy first, and do not pass its path into the actor.
        original_run = worker.run

        def run_worker(request):
            nonlocal session_open
            if session_open:
                settle_session(store, name)
                session_open = False
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
            try:
                return original_run(request)
            finally:
                os.environ["CLAUDE_CONFIG_DIR"] = str(session)

        worker.run = run_worker
        goal = (project / "issue.md").read_text(encoding="utf-8")
        heading = next(line for line in goal.splitlines() if line.startswith("# "))
        lines = (project / "public_check.py").read_text(encoding="utf-8").splitlines()
        assertion = next(line for line in lines
                         if line.lstrip().startswith("assert ") and lines.count(line) == 1)
        source = next(path for path in task["editable_paths"] if path != "report.json")
        result = controller_workflow.execute(
            executor, root_id, issue="issue.md",
            source_paths=list(dict.fromkeys(["issue.md", "app.py",
                                                   "public_check.py", source])),
            quote_requests=[{"source": "issue.md", "quote": heading},
                            {"source": "public_check.py", "quote": assertion}],
            interpreter=interpreter,
            operational={"context_tokens": 1000, "deadline_seconds": None,
                         "prior_local_repairs": 0,
                         "required_artefacts": task["editable_paths"],
                         "deadline": None, "authorised_task_budget_usd": 12.0,
                         "observed_at": "2026-09-28T00:00:00Z"},
            assessment_allowance_usd=0.5,
            controller_adapter=controller,
            explicit_mode="on")
    except BaseException as exc:
        error = type(exc).__name__ + ": " + str(exc)[:600]
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
    finally:
        if session_open:
            try:
                settle_session(store, name)
                session_open = False
            except Exception as exc:
                error = (error + "; " if error else "") + (
                    "credential reconciliation required: " + str(exc)[:400])
        os.environ.pop("CLAUDE_CONFIG_DIR", None)
        state = executor.status(root_id)
        public = state.get("public_assessment") or {}
        routing = state.get("routing_decision") or {}
        dispatch = result.get("dispatch") if isinstance(result, dict) else None
        receipt = {
            "schema_version": 1,
            "status": state["state"], "error": error,
            "root_id": root_id, "seed": str(project),
            "credential_reconciled": not session_open,
            "public_assessment_status": public.get("status"),
            "public_assessment_cost_usd": (public.get("result") or {}).get(
                "telemetry", {}).get("cost_usd"),
            "effective_action": (routing.get("decision") or {}).get("effective_action"),
            "controller_stage": dispatch.get("stage") if dispatch else None,
            "worker_attempt_count": len(state.get("attempts", [])),
            "budget": state["budget"],
        }
        OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
        print(json.dumps({key: receipt[key] for key in
                          ("status", "error", "credential_reconciled",
                           "public_assessment_status", "effective_action",
                           "controller_stage", "worker_attempt_count")},
                         sort_keys=True))
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
