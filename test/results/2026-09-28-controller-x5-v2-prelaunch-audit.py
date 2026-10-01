#!/usr/bin/env python3
"""Read-only proof that the frozen X5 v2 canary stopped before Claude launch.

Run as root in the project's kali-linux WSL instance. This reads no secret
bytes and deliberately does not change the uncertain budget ledger.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_wsl_q1 as q1  # noqa: E402


MANIFEST = ROOT / "test/results/2026-09-28-controller-x5-screen-manifest-v2.json"
NOTICE = ROOT / "test/results/2026-09-28-controller-x5-v2-canary-notice.json"
ADAPTER = ROOT / "test/results/2026-09-28-controller-x5-worker-adapter-v2-source.py"
CANARY = ROOT / "test/results/2026-09-28-controller-x5-host-canary-v2-source.py"
LAUNCHER_SOURCE = ROOT / "tools/worker_wsl_namespace_q3.sh"
LAUNCHER_INSTALLED = Path("/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace-q3")
INVOCATION = "a4cbcbe94af591785346d440ac2bbc62"
ACTOR_NAME = f"q1-{INVOCATION}"
LEDGER = (q1.SEEDS / "x5-high-canary-d5b8c015f294" /
          ".claude/x5-high-budget.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if q1.os.geteuid() != 0:
        raise RuntimeError("WSL root is required for private Q1 evidence")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    notice = json.loads(NOTICE.read_text(encoding="utf-8"))
    files = manifest["runtime_package"]["files"]
    for path, frozen in (
        (ADAPTER, "tools/controller_x5_worker_adapter.py"),
        (CANARY, "tools/controller_x5_host_canary.py"),
        (LAUNCHER_SOURCE, "tools/worker_wsl_namespace_q3.sh"),
    ):
        if digest(path) != files[frozen]:
            raise RuntimeError(f"frozen source differs: {frozen}")
    if (notice["manifest_sha256"] != manifest["manifest_sha256"]
            or notice["requested_cell"] != "worker-sonnet-high"):
        raise RuntimeError("canary notice is not the frozen Sonnet High request")
    installed_hash = digest(LAUNCHER_INSTALLED)
    if installed_hash != digest(LAUNCHER_SOURCE):
        raise RuntimeError("installed Q3 launcher differs from frozen source")
    shell = LAUNCHER_SOURCE.read_text(encoding="utf-8")
    guard = shell.index("$7 == claude-sonnet-5 && $9 == low")
    auth = shell.index('worker_wsl_q3_auth.py" begin')
    start = shell.index('worker_wsl_q1.py" start')
    if not (guard < auth < start):
        raise RuntimeError("launcher preflight order changed")
    if "$7 == claude-sonnet-5 && $9 == high" in shell[guard:auth]:
        raise RuntimeError("Q3 launcher unexpectedly admits Sonnet High")

    record = q1.load_record(ACTOR_NAME)
    record_path = q1.record_path(ACTOR_NAME)
    if (LAUNCHER_INSTALLED.stat().st_mtime_ns >= record_path.stat().st_mtime_ns
            or (q1.MANIFESTS / f"{ACTOR_NAME}.start.json").exists()
            or (q1.MANIFESTS / f"{ACTOR_NAME}.stop.json").exists()
            or (Path("/var/lib/orchestrator-worker-n4/auth/sessions") /
                ACTOR_NAME).exists()):
        raise RuntimeError("prelaunch absence or launcher age is unproven")
    state = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = state["invocations"][INVOCATION]
    if (row["state"] != "uncertain" or row["cost_usd"] is not None
            or row["resolution"]["final"] is not False
            or row["resolution"]["cost_usd"] is not None):
        raise RuntimeError("historical uncertain ledger changed")
    print(json.dumps({
        "schema_version": 1,
        "manifest_sha256": manifest["manifest_sha256"],
        "invocation_id": INVOCATION,
        "q1_record_sha256": record["record_sha256"],
        "q1_start_present": False,
        "q1_stop_present": False,
        "auth_session_present": False,
        "installed_q3_launcher_sha256": installed_hash,
        "installed_launcher_predates_q1_record": True,
        "frozen_request_cell": notice["requested_cell"],
        "guard_rejects_cell_before_auth_and_start": True,
        "provider_invocations_inferred": 0,
        "provider_reported_cost_usd": None,
        "ledger_state": row["state"],
        "local_hold_usd": row["allowance_units"] / 1_000_000_000,
        "ledger_mutated": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
