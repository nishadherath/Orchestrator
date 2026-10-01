#!/usr/bin/env python3
"""Check Q3 Claude.ai login inside one Q1 actor without a model request.

Only Boolean results leave this process. A failed or ambiguous credential
handoff is retained for reconciliation by the root-owned credential store.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

RUNTIME = Path("/opt/orchestrator-worker-runtime")
sys.path.insert(0, str(RUNTIME))
from worker_wsl_auth import AuthError, CredentialStore  # noqa: E402
from worker_wsl_q1 import ACTORS, MANIFESTS, OUTPUTS, SEEDS, collect, stage  # noqa: E402
from worker_wsl_q2_verify import copy_package, dispose  # noqa: E402

LAUNCHER = RUNTIME / "bin/worker-wsl-namespace-q3"
CLAUDE = RUNTIME / "bin/claude"


def run(source: Path) -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("Q3 auth probe requires WSL root")
    try:
        CredentialStore().inspect()
    except AuthError:
        return {"result": "BLOCKED_AUTH", "credential_current": False,
                "provider_calls": 0, "provider_cost_usd": 0}

    package, spec_path, _ = copy_package(source, None)
    name = "q1-" + uuid.uuid4().hex
    actor = ACTORS / name
    staged = False
    stopped = False
    try:
        stage(package, spec_path, name)
        staged = True
        process = subprocess.run(
            [str(LAUNCHER), "--subscription", str(actor), "--", str(CLAUDE),
             "--restricted", "auth", "status", "--json"],
            cwd="/", capture_output=True, text=True, timeout=45)
        stopped = (MANIFESTS / f"{name}.stop.json").is_file()
        if process.returncode or not stopped:
            return {"result": "BLOCKED_AUTH", "credential_current": False,
                    "isolated_login": False, "provider_calls": 0,
                    "provider_cost_usd": 0}
        status = json.loads(process.stdout)
        collect(name, package)
        CredentialStore().inspect()
        checks = {
            "isolated_claude_login": status.get("loggedIn") is True
            and status.get("authMethod") == "claude.ai",
            "subscription_reported": status.get("subscriptionType")
            in {"pro", "max", "team", "enterprise"},
            "credential_reconciled": True,
            "q1_writer_stopped": stopped,
        }
        return {"result": "PASS" if all(checks.values()) else "BLOCKED_AUTH",
                "checks": checks, "credential_current": all(checks.values()),
                "provider_calls": 0, "provider_cost_usd": 0}
    finally:
        # Never erase an actor whose process/stop state is uncertain. Its
        # identity and the private credential session need reconciliation.
        if not staged or stopped:
            if staged:
                dispose(actor, ACTORS)
                dispose(OUTPUTS / name, OUTPUTS)
                for suffix in (".json", ".start.json", ".stop.json"):
                    (MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)
            dispose(package, SEEDS)
            spec_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.source)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__,
                          "provider_calls": 0, "provider_cost_usd": 0}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
