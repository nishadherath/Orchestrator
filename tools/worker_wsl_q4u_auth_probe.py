#!/usr/bin/env python3
"""Check Q4U Claude.ai subscription authentication without a model request."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


def run(repo: Path) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("Q4U authentication probe requires WSL root")
    sys.path.insert(0, str(repo / "tools"))
    from worker_q4u_public import ROOT
    from worker_wsl_q1 import SEEDS, collect
    from worker_wsl_q4u import stage
    from worker_wsl_q4u_adapter import public_source
    from worker_wsl_q4u_adapter import LAUNCHER

    task = json.loads((ROOT / "test/fixtures/worker_q4u_public/M05/task.json").read_text(encoding="utf-8"))
    name = "q1-" + uuid.uuid4().hex
    claude = "/opt/orchestrator-worker-runtime/bin/claude"
    with tempfile.TemporaryDirectory(prefix="q4u-auth-probe-", dir=SEEDS) as raw:
        workspace = Path(raw)
        source = ROOT / "test/fixtures/worker_q4u_public/M05/actor"
        for relative in task["actor_files"]:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / relative).read_bytes())
        package, manifest_path, _ = public_source(workspace, task)
        try:
            staged = stage(package, manifest_path, name)
            actor = Path(staged["actor_root"])
            process = subprocess.run(
                [str(LAUNCHER), "--subscription", str(actor), "--", claude,
                 "--restricted", "auth", "status", "--json"],
                cwd="/", capture_output=True, text=True, timeout=60)
            # An auth/launcher failure may happen before an actor starts. In
            # that case Q1 has no collection record; keep the auth failure as
            # the primary diagnosis instead of masking it with collect().
            if process.returncode:
                raise RuntimeError("isolated Q4U Claude auth status failed")
            collected = collect(name, package)
            if collected["writer_exit_status"] != 0:
                raise RuntimeError("isolated Q4U Claude auth status failed")
            status = json.loads(process.stdout)
        finally:
            shutil.rmtree(package, ignore_errors=True)
            manifest_path.unlink(missing_ok=True)
    checks = {"logged_in": status.get("loggedIn") is True,
              "claude_ai": status.get("authMethod") == "claude.ai",
              "subscription": status.get("subscriptionType") in
                  {"pro", "max", "team", "enterprise"},
              "no_model_request": True}
    return {"schema_version": 1,
            "result": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks, "provider_calls": 0, "provider_cost_usd": 0,
            "auth_method": status.get("authMethod"),
            "subscription_type": status.get("subscriptionType")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = run(args.repo)
    except (OSError, ValueError, KeyError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        return 1
    print(json.dumps(value, sort_keys=True))
    return 0 if value["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
