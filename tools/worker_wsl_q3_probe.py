#!/usr/bin/env python3
"""Provider-free Q3 launcher checks; never passes a valid paid command."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

RUNTIME = Path("/opt/orchestrator-worker-runtime")
sys.path.insert(0, str(RUNTIME))
from worker_wsl_q1 import ACTORS, MANIFESTS, OUTPUTS, SEEDS, collect, stage  # noqa: E402
from worker_wsl_q2_verify import copy_package, dispose  # noqa: E402

LAUNCHER = RUNTIME / "bin/worker-wsl-namespace-q3"
AUTH = RUNTIME / "worker_wsl_q3_auth.py"


def run(source: Path) -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("Q3 probe requires WSL root")
    package, manifest_path, _ = copy_package(source, None)
    name = "q1-" + uuid.uuid4().hex
    actor = ACTORS / name
    auth_session = Path("/var/lib/orchestrator-worker-n4/auth/sessions") / name
    started = False
    stopped = False
    try:
        staged = stage(package, manifest_path, name)
        started = True
        bad = subprocess.run([str(LAUNCHER), "--subscription", str(actor), "--",
                              "/usr/bin/true"], capture_output=True, text=True,
                             timeout=30)
        rejected_before_auth = (bad.returncode == 64 and not auth_session.exists()
                                and not (MANIFESTS / f"{name}.start.json").exists())
        wrong_name = subprocess.run(["python3", str(AUTH), "begin", "inv-" + uuid.uuid4().hex],
                                    capture_output=True, text=True, timeout=10)
        wrapper_rejected_n4_name = wrong_name.returncode == 64
        process = subprocess.run([str(LAUNCHER), str(actor), "--", "/usr/bin/true"],
                                 capture_output=True, text=True, timeout=30)
        stopped = (MANIFESTS / f"{name}.stop.json").is_file()
        receipt = collect(name, package) if process.returncode == 0 and stopped else None
        output = OUTPUTS / name
        collected_unchanged = (receipt is not None and receipt["changed_paths"] == []
                               and all(hashlib.sha256((output / row["path"]).read_bytes()).hexdigest()
                                       == row["sha256"] for row in staged_spec(manifest_path)["files"]))
        checks = {"invalid_subscription_command_rejected_before_auth": rejected_before_auth,
                  "credential_wrapper_rejects_n4_identity": wrapper_rejected_n4_name,
                  "uncredentialed_actor_stopped": process.returncode == 0 and stopped,
                  "unchanged_package_collected": collected_unchanged,
                  "no_provider_call": True}
        return {"result": "PASS" if all(checks.values()) else "FAIL",
                "checks": checks, "provider_calls": 0, "provider_cost_usd": 0}
    finally:
        if started and stopped:
            dispose(actor, ACTORS)
            dispose(OUTPUTS / name, OUTPUTS)
            for suffix in (".json", ".start.json", ".stop.json"):
                (MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)
            dispose(package, SEEDS)
            manifest_path.unlink(missing_ok=True)


def staged_spec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.source)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:500]}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
