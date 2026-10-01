"""Settle the pre-launch H02b launcher budget rejection at zero without replay."""

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02b_producer as h02  # noqa: E402
import worker_wsl_q1 as q1  # noqa: E402


OUT = h02.RUN_DIR / "reconciliation.json"


def active_writer(invocation: str) -> list[int]:
    found = []
    for path in Path("/proc").iterdir():
        if not path.name.isdecimal() or int(path.name) == os.getpid():
            continue
        try:
            command = (path / "cmdline").read_bytes().replace(b"\0", b" ")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if invocation.encode() in command:
            found.append(int(path.name))
    return found


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("H02b reconciliation requires WSL root")
    row = h02.manifest()
    executor = h02.entry(row)
    root = h02.root_id(row)
    status = executor.status(root)
    if status["state"] != "uncertain" or len(status["attempts"]) != 1:
        raise RuntimeError("H02 root is not the single uncertain attempt")
    invocation = status["attempts"][0]["invocation_id"]
    receipt = status["attempts"][0].get("receipt") or {}
    if (receipt.get("returncode") != 64 or receipt.get("terminal") is not False
            or receipt.get("cost_usd") is not None
            or receipt.get("q4t_diagnostics", {}).get("stdout_bytes") != 0):
        raise RuntimeError("H02b receipt does not prove pre-launch rejection")
    name = "q1-" + invocation
    start = q1.MANIFESTS / f"{name}.start.json"
    stop = q1.MANIFESTS / f"{name}.stop.json"
    auth = Path("/var/lib/orchestrator-worker-n4/auth/sessions") / name
    writers = active_writer(invocation)
    if start.exists() or stop.exists() or auth.exists() or writers:
        raise RuntimeError("H02 launch or writer evidence is not terminal")
    if not (q1.MANIFESTS / f"{name}.json").is_file():
        raise RuntimeError("H02 stage manifest is missing")
    evidence = {"schema_version": 1, "case": "H02b",
                "manifest_sha256": row["manifest_sha256"],
                "root_id": root, "invocation_id": invocation,
                "stage_manifest_present": True, "start_receipt_present": False,
                "stop_receipt_present": False, "auth_session_present": False,
                "active_writer_pids": writers,
                "reproduced_prelaunch_failure": "Q4U launcher rejects USD 5 single-call allowance above USD 4 ceiling",
                "settled_api_equivalent_usd": 0.0,
                "provider_call_observed": False}
    h02.exclusive(OUT, evidence)
    after = executor.reconcile_uncertain(
        root, actor="x5-h02-reconciliation",
        reason="pre-launch Q4U budget validation exit 64; no start or auth session",
        cost_usd=0.0,
        evidence="h02b-reconciliation:" + row["manifest_sha256"],
        writers_stopped=True)
    print(json.dumps({"state": after["state"],
                      "spent_usd": after["budget"]["spent_usd"],
                      "unresolved": after["budget"]["unresolved"],
                      "evidence": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
