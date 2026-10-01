#!/usr/bin/env python3
"""Provider-free WSL root preflight for one X4 Controller-to-worker smoke.

This is a local experiment driver, not a consumer entrypoint. It copies only
the public N04-D1 actor into the root-owned seed area and never reads an
oracle or prints a credential.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator")
sys.path.insert(0, str(ROOT / "tools"))

from task_executor import TaskExecutor  # noqa: E402
from worker_wsl_auth import CredentialStore  # noqa: E402
from worker_wsl_q1 import SEEDS  # noqa: E402
from worker_wsl_q3_adapter import Q3WslAdapter, isolated_public_runner  # noqa: E402

FIXTURE = ROOT / "test/fixtures/controller_x3/development/N04-D1/actor"
CLAUDE = "/opt/orchestrator-worker-runtime/bin/claude"
OUT = ROOT / "test/results/2026-09-28-controller-x4-wsl-preflight-v3.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if os.geteuid() != 0 or not FIXTURE.is_dir() or not SEEDS.is_dir():
        raise RuntimeError("root WSL runtime or public fixture is unavailable")
    store = CredentialStore()
    store.inspect()
    with tempfile.TemporaryDirectory(prefix="x4-auth-check-", dir=store.base) as raw:
        private = Path(raw)
        private.chmod(0o700)
        token = private / ".credentials.json"
        token.write_bytes(store.master.read_bytes())
        token.chmod(0o600)
        env = {key: value for key, value in os.environ.items()
               if key not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                              "CLAUDE_CODE_OAUTH_TOKEN")}
        env["CLAUDE_CONFIG_DIR"] = str(private)
        status = subprocess.run([CLAUDE, "auth", "status", "--json"],
                                capture_output=True, text=True, timeout=30,
                                env=env)
        login = json.loads(status.stdout)
        if (status.returncode or login.get("loggedIn") is not True
                or login.get("authMethod") != "claude.ai"):
            raise RuntimeError("private Controller credential preflight failed")

    seed = Path(tempfile.mkdtemp(prefix="controller-x4-", dir=SEEDS))
    try:
        shutil.copytree(FIXTURE, seed, dirs_exist_ok=True)
        seed.chmod(0o700)
        acceptance = json.loads((seed / "acceptance.json").read_text(encoding="utf-8"))
        editable = acceptance["editable_paths"]
        files = {path.relative_to(seed).as_posix(): sha(path)
                 for path in seed.rglob("*") if path.is_file()}
        task = {"actor_files": files, "editable_paths": editable}
        adapter = Q3WslAdapter(task)
        capability = adapter.capability(seed)
        contract = seed / "n1-acceptance.json"
        contract.write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["public check passes"],
            "constraints": [], "required_outputs": editable,
            "protected_paths": ["issue.md", "app.py", "public_check.py"],
            "command": ["python3", "-B", "public_check.py"],
            "timeout_s": 30,
        }), encoding="utf-8")
        executor = TaskExecutor(seed, adapter,
                                command_runner=isolated_public_runner(task))
        root = executor.admit(
            goal=(seed / "issue.md").read_text(encoding="utf-8"),
            scope=editable, permissions=["read", "edit"],
            input_paths=["issue.md", "app.py", "public_check.py"],
            acceptance_path=contract, budget_usd=12.0,
            authority_id="x4-live-smoke-grant", actor="operator",
            root_id="x4-live-smoke-root-v3")
        state = executor.status(root)
        if state["state"] != "ready":
            raise RuntimeError("N1 root did not reach ready state")
        receipt = {
            "schema_version": 1, "status": "READY_NO_PROVIDER_CALL",
            "seed": str(seed), "root_id": root,
            "actor_files": files, "editable_paths": editable,
            "credential_method": "claude.ai subscription",
            "credential_fresh": True, "provider_calls": 0,
            "worker_capability": {
                "enforcement_proven": capability["enforcement_proven"],
                "budget_enforced": capability["budget_enforced"],
                "supported_cells": capability["supported_cells"],
            },
        }
        OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
        print(json.dumps({key: receipt[key] for key in
                          ("status", "seed", "root_id", "provider_calls")},
                         sort_keys=True))
        return 0
    except BaseException:
        # The seed has never hosted a provider call when this preflight fails.
        shutil.rmtree(seed)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
