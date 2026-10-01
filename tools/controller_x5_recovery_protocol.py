"""Public-only eligibility and single-use twin snapshots for X5 recovery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable


PUBLIC_FILES = {
    "R01": {"acceptance.json", "app.py", "delivery.py", "issue.md", "journal.py",
            "public_check.py", "report.json", "trace.json"},
    "R02": {"acceptance.json", "app.py", "cache.py", "decision.py", "issue.md",
            "policy.py", "public_check.py", "report.json", "trace.json"},
}
TERMINAL = {"accepted", "partial", "failed", "blocked"}


class RecoveryStop(ValueError):
    """Producer or snapshot is not safe to continue."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def public_files(actor: Path, task_id: str) -> dict[str, bytes]:
    if task_id not in PUBLIC_FILES or actor.is_symlink() or not actor.is_dir():
        raise RecoveryStop("unknown task or redirected actor")
    files = {}
    for name in PUBLIC_FILES[task_id]:
        path = actor / name
        if path.is_symlink() or not path.is_file():
            raise RecoveryStop(f"missing or redirected public file: {name}")
        files[name] = path.read_bytes()
    extra = {path.name for path in actor.iterdir()} - PUBLIC_FILES[task_id]
    if extra - {".claude", "__pycache__"}:
        raise RecoveryStop("unexpected actor file")
    if any((actor / name).is_symlink() for name in extra):
        raise RecoveryStop("actor metadata contains a redirected path")
    return files


def qualify(task_id: str, actor: Path, state: dict,
            public_runner: Callable | None = None) -> dict:
    """Use only settled executor state and public actor evidence."""
    files = public_files(actor, task_id)
    budget = state.get("budget") or {}
    attempts = state.get("attempts") or []
    if (not isinstance(state.get("root_id"), str) or not state["root_id"]
            or state.get("state") not in TERMINAL or not attempts
            or not isinstance(budget.get("unresolved"), list)
            or budget["unresolved"]
            or budget.get("breached") is not False
            or type(budget.get("spent_usd")) not in (int, float)
            or not 0 < budget["spent_usd"] <= budget.get("limit_usd", -1)):
        raise RecoveryStop("producer is not a settled bounded terminal attempt")
    costs = []
    for attempt in attempts:
        receipt = attempt.get("receipt") or {}
        if (attempt.get("process_state") != "terminal"
                or attempt.get("late_receipts")
                or attempt.get("receipt_digest") is None
                or receipt.get("terminal") is not True
                or receipt.get("writer_stopped") is not True
                or receipt.get("identity_valid") is not True
                or not receipt.get("actual_model")
                or type(receipt.get("cost_usd")) not in (int, float)
                or receipt["cost_usd"] <= 0):
            raise RecoveryStop("producer receipt or worker identity is unsettled")
        costs.append(receipt["cost_usd"])
    if abs(sum(costs) - budget["spent_usd"]) > 1e-8:
        raise RecoveryStop("producer charge differs from settled receipts")
    try:
        report = json.loads(files["report.json"])
    except (ValueError, UnicodeDecodeError) as exc:
        raise RecoveryStop("producer report is not valid JSON") from exc
    if not isinstance(report, dict):
        raise RecoveryStop("producer report is invalid")
    if public_runner is None:
        check = subprocess.run([sys.executable, "-B", "public_check.py"], cwd=actor,
                               capture_output=True, text=True, timeout=15, check=False)
    else:
        check = public_runner(["python3", "-B", "public_check.py"], cwd=actor,
                              capture_output=True, timeout=30, shell=False)
    stdout = check.stdout.decode() if isinstance(check.stdout, bytes) else check.stdout
    stderr = check.stderr.decode() if isinstance(check.stderr, bytes) else check.stderr
    if check.returncode not in {0, 1} or (check.returncode == 1 and "AssertionError" not in stderr):
        raise RecoveryStop("public check did not return a verdict")
    unresolved = report.get("probes")
    concrete = (isinstance(unresolved, list)
                and any(isinstance(row, dict) and row.get("passed") is False
                        and isinstance(row.get("command"), str) and row["command"].strip()
                        for row in unresolved))
    eligible = check.returncode == 1 or (
        report.get("completion_claim") in {"partial", "blocked"} and concrete)
    if not eligible:
        raise RecoveryStop("no publicly observable unresolved work")
    return {"schema_version": 1, "task_id": task_id,
            "producer_root_id": state.get("root_id"),
            "producer_cost_usd": budget["spent_usd"],
            "public_check_exit_code": check.returncode,
            "public_check_output_sha256": digest((stdout + stderr).encode()),
            "actor_sha256": {name: digest(data) for name, data in sorted(files.items())}}


def twins(task_id: str, actor: Path, state: dict, destination: Path,
          public_runner: Callable | None = None) -> dict:
    """Clone the same public bytes to two fresh, single-use successor roots."""
    record = qualify(task_id, actor, state, public_runner)
    files = public_files(actor, task_id)
    if {name: digest(data) for name, data in sorted(files.items())} != record["actor_sha256"]:
        raise RecoveryStop("actor changed after eligibility check")
    if destination.exists() or destination.is_symlink():
        raise RecoveryStop("successor destination is already used")
    destination.mkdir(parents=True, mode=0o700)
    try:
        for arm in ("S", "A"):
            root = destination / arm
            root.mkdir(mode=0o700)
            for name, data in files.items():
                (root / name).write_bytes(data)
            if {name: digest((root / name).read_bytes()) for name in files} != record["actor_sha256"]:
                raise RecoveryStop("successor snapshot differs")
        (destination / "snapshot.json").write_text(
            json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return record
    except Exception:
        shutil.rmtree(destination)
        raise
