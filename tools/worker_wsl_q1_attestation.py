#!/usr/bin/env python3
"""Bind Q1's provider-free WSL probe and root ledger to exact runtime bytes."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import dispatch_budget
import worker_wsl_attestation as n4

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "test/results/2026-09-25-worker-q1-wsl-host.json"
SOURCES = {
    "tools/worker_wsl_q1.py": "/opt/orchestrator-worker-runtime/worker_wsl_q1.py",
    "tools/worker_wsl_q1_actor_probe.py": "/opt/orchestrator-worker-runtime/worker_wsl_q1_actor_probe.py",
    "tools/worker_wsl_q1_probe.py": "/opt/orchestrator-worker-runtime/worker_wsl_q1_probe.py",
    "tools/worker_wsl_namespace_q1.sh": "/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace-q1",
}
EXPECTED = {
    "absolute_path_rejected", "actor_probe_passed", "actor_uid",
    "backslash_path_rejected", "collected_content_matches_actor",
    "collection_before_stop_rejected", "concurrent_source_change_rejected",
    "drift_actor_stopped", "drift_no_output", "duplicate_collection_rejected",
    "editable_helper", "editable_main", "evaluator_direct_denied",
    "evaluator_symlink_denied", "graft_evaluator_absent",
    "graft_parent_escape_rejected", "graft_sees_both_modules",
    "graft_six_tools", "namespace_stopped", "new_nested_file_denied",
    "new_root_file_denied", "protected_acceptance",
    "protected_actor_change_rejected", "protected_issue",
    "protected_output_unchanged", "protected_public_check",
    "race_actor_stopped", "race_no_output", "receipt_bound_to_manifest",
    "sanitised_env", "sibling_actor_denied", "source_symlink_rejected",
    "source_unchanged", "traversal_path_rejected",
    "two_allowed_edits_collected", "undeclared_source_file_rejected",
    "windows_mount_hidden", "wsl_login_hidden",
}
ACCOUNTING_EXPECTED = {"reservation_preceded_launch", "zero_charge_settled",
                       "duplicate_launch_rejected", "unknown_charge_retains_hold",
                       "hold_blocks_new_dispatch"}


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wsl(*args: str, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(["wsl.exe", "-u", "root", "--", *args],
                          capture_output=True, text=True, timeout=timeout)


def runtime_hashes() -> dict[str, str]:
    result = wsl("sha256sum", *SOURCES.values(), timeout=90)
    if result.returncode:
        raise RuntimeError("Q1 WSL runtime hashes unavailable: " + result.stderr[-300:])
    rows = [line.split() for line in result.stdout.splitlines()]
    if len(rows) != len(SOURCES) or any(len(row) != 2 for row in rows):
        raise RuntimeError("Q1 WSL runtime hash inventory is incomplete")
    return {source: row[0] for source, row in zip(SOURCES, rows, strict=True)}


def sources() -> dict[str, str]:
    return {path: sha(ROOT / path) for path in (*SOURCES, "tools/worker_wsl_q1_install.sh",
                                            "tools/worker_wsl_q1_attestation.py")}


def host_digest() -> str:
    host = json.loads(n4.OUTPUT.read_text(encoding="utf-8"))
    if not n4.validate(host, check_host=True):
        raise RuntimeError("N4 WSL host attestation is stale")
    return host["evidence_sha256"]


def validate(value: dict, *, check_host: bool) -> bool:
    try:
        body = {key: item for key, item in value.items() if key != "evidence_sha256"}
        if (value["result"] != "PASS" or value["evidence_sha256"] != digest(body)
                or value["source_sha256"] != sources()
                or value["n4_host_evidence_sha256"] != host_digest()
                or set(value["probe"]["checks"]) != EXPECTED
                or value["probe"]["result"] != "PASS"
                or value["probe"]["check_count"] != len(EXPECTED)
                or not all(value["probe"]["checks"].values())
                or value["probe"]["provider_calls"] != 0
                or value["probe"]["provider_cost_usd"] != 0
                or set(value["accounting_checks"]) != ACCOUNTING_EXPECTED
                or not all(value["accounting_checks"].values())):
            return False
        if check_host and value["runtime_sha256"] != runtime_hashes():
            return False
        return True
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        return False


def run() -> dict:
    source_sha256 = sources()
    runtime_sha256 = runtime_hashes()
    if any(source_sha256[path] != runtime_sha256[path] for path in SOURCES):
        raise RuntimeError("installed Q1 runtime differs from source; run worker_wsl_q1_install.sh")
    n4_digest = host_digest()
    with tempfile.TemporaryDirectory(prefix="worker-q1-accounting-") as directory:
        budget = dispatch_budget.DispatchBudget(Path(directory) / "budget.json", 1.0,
                                                scope="task_dispatch")
        invocation = "q1-probe-" + uuid.uuid4().hex
        budget.reserve(invocation, 1.0, 1.0,
                       {"purpose": "provider-free Q1 WSL boundary", "source_sha256": source_sha256})
        budget.start(invocation)
        try:
            process = wsl("python3", "/opt/orchestrator-worker-runtime/worker_wsl_q1_probe.py")
            probe = json.loads(process.stdout.strip())
        except (OSError, ValueError, subprocess.TimeoutExpired):
            budget.settle(invocation, None, final=False,
                          telemetry={"provider_calls": 0}, evidence="Q1 probe outcome unknown")
            raise
        if (process.returncode or probe.get("result") != "PASS"
                or set(probe.get("checks", {})) != EXPECTED
                or not all(probe["checks"].values())
                or probe.get("provider_calls") != 0
                or probe.get("provider_cost_usd") != 0):
            budget.settle(invocation, None, final=False,
                          telemetry={"provider_calls": 0}, evidence="Q1 probe did not pass")
            raise RuntimeError("Q1 WSL probe failed: " + (process.stderr + process.stdout)[-700:])
        budget.settle(invocation, 0.0, final=True,
                      telemetry={"provider_calls": 0, "check_count": len(EXPECTED)},
                      evidence="Q1 WSL probe PASS with stopped writer and zero provider calls")
        snapshot = budget.snapshot()
        accounting_checks = {
            "reservation_preceded_launch": snapshot["invocations"][invocation]["started_at"] is not None,
            "zero_charge_settled": snapshot["spent_usd"] == 0
                                   and snapshot["reserved_usd"] == 0
                                   and snapshot["unresolved"] == [],
        }
        try:
            budget.start(invocation)
        except dispatch_budget.InvocationAlreadyStarted:
            accounting_checks["duplicate_launch_rejected"] = True
        else:
            accounting_checks["duplicate_launch_rejected"] = False
        uncertain = "q1-unknown-" + uuid.uuid4().hex
        budget.reserve(uncertain, 1.0, 1.0, {"purpose": "uncertain-charge hold probe"})
        budget.start(uncertain)
        budget.settle(uncertain, None, final=False, telemetry={}, evidence="synthetic uncertain outcome")
        held = budget.snapshot()
        accounting_checks["unknown_charge_retains_hold"] = (
            held["reserved_usd"] == 1.0 and uncertain in held["unresolved"]
            and held["available_usd"] == 0)
        try:
            budget.reserve("q1-third-" + uuid.uuid4().hex, 1.0, 1.0, {})
        except dispatch_budget.BudgetExhausted:
            accounting_checks["hold_blocks_new_dispatch"] = True
        else:
            accounting_checks["hold_blocks_new_dispatch"] = False
    result = {"schema_version": 1, "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "result": "PASS" if all(accounting_checks.values()) else "FAIL",
              "source_sha256": source_sha256, "runtime_sha256": runtime_sha256,
              "n4_host_evidence_sha256": n4_digest,
              "probe": probe, "accounting_checks": accounting_checks,
              "scope": "provider-free Q1 multi-file WSL boundary; no paid adapter qualified"}
    result["evidence_sha256"] = digest(result)
    if not validate(result, check_host=True):
        raise RuntimeError("Q1 attestation failed self-validation")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            value = json.loads(OUTPUT.read_text(encoding="utf-8"))
            if not validate(value, check_host=True):
                raise RuntimeError("stored Q1 attestation is stale or invalid")
            print("PASS: Q1 WSL attestation current")
        else:
            value = run()
            print(f"PASS: {len(value['probe']['checks'])} WSL checks and "
                  f"{len(value['accounting_checks'])} accounting checks; "
                  f"evidence {value['evidence_sha256']}")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError,
            subprocess.TimeoutExpired) as exc:
        print(f"Q1 attestation rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
