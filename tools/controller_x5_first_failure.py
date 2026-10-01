"""Public, settled first-failure checkpoint for a matched X5 comparison.

The producer has made exactly one B0 worker call. Both successors start from
the same actor bytes and are limited to one Sonnet local repair call.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
from typing import Callable

import acceptance
import model_registry


class CheckpointStop(ValueError):
    """The producer or actor cannot be safely compared."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def actor_files(actor: Path, names: set[str]) -> dict[str, bytes]:
    if (not isinstance(names, set) or not names
            or "public_check.py" not in names or "acceptance.json" not in names
            or any(not isinstance(name, str) or not name or "\\" in name or ":" in name
                   or PurePosixPath(name).is_absolute()
                   or any(part in {"", ".", ".."} or part.startswith(".")
                          for part in PurePosixPath(name).parts)
                   for name in names)
            or actor.is_symlink() or not actor.is_dir()):
        raise CheckpointStop("invalid public actor file set")
    observed = set()

    def inventory(directory: Path) -> None:
        for path in directory.iterdir():
            if path.is_symlink():
                raise CheckpointStop("redirected actor path")
            if ((directory == actor and path.name == ".claude")
                    or path.name == "__pycache__"):
                if not path.is_dir():
                    raise CheckpointStop("actor metadata is not a directory")
                continue
            if path.is_dir():
                inventory(path)
            elif path.is_file():
                observed.add(path.relative_to(actor).as_posix())
            else:
                raise CheckpointStop("unexpected actor entry")

    inventory(actor)
    if observed != names:
        raise CheckpointStop("actor file inventory differs from the frozen package")
    files = {}
    for name in names:
        path = actor / name
        if not path.is_file():
            raise CheckpointStop(f"missing or redirected public file: {name}")
        files[name] = path.read_bytes()
    return files


def qualify(actor: Path, names: set[str], state: dict,
            public_runner: Callable | None = None) -> dict:
    """Reject every checkpoint without one failed, settled public B0 call."""
    files = actor_files(actor, names)
    attempts = state.get("attempts")
    budget = state.get("budget") or {}
    admission = state.get("admission") or {}
    ladder = state.get("ladder")
    if (not isinstance(state.get("root_id"), str) or not state["root_id"]
            or state.get("state") != "ready" or admission.get("policy") != "B0"
            or not isinstance(ladder, list) or len(ladder) < 2
            or ladder[:2] != ["worker-sonnet-low", "worker-sonnet-low"]
            or not isinstance(attempts, list) or len(attempts) != 1
            or not isinstance(budget.get("unresolved"), list) or budget["unresolved"]
            or budget.get("breached") is not False
            or type(budget.get("spent_usd")) not in (int, float)
            or type(budget.get("limit_usd")) not in (int, float)
            or not 0 < budget["spent_usd"] <= budget["limit_usd"]):
        raise CheckpointStop("not a bounded first-failure B0 checkpoint")
    attempt = attempts[0]
    receipt = attempt.get("receipt") or {}
    verification = attempt.get("verification")
    frozen = (state.get("definition") or {}).get("acceptance_definition") or {}
    evidence = verification.get("evidence") if isinstance(verification, dict) else None
    command = evidence.get("command") if isinstance(evidence, dict) else None
    artefacts = evidence.get("artefacts") if isinstance(evidence, dict) else None
    if (attempt.get("sequence") != 1
            or attempt.get("requested_cell") != ladder[0]
            or attempt.get("process_state") != "terminal"
            or attempt.get("late_receipts")
            or not isinstance(attempt.get("receipt_digest"), str)
            or not attempt["receipt_digest"]
            or receipt.get("terminal") is not True
            or receipt.get("writer_stopped") is not True
            or receipt.get("identity_valid") is not True
            or model_registry.model_class_for_provider_id(
                receipt.get("actual_model")) != "sonnet"
            or type(receipt.get("cost_usd")) not in (int, float)
            or receipt["cost_usd"] <= 0
            or abs(receipt["cost_usd"] - budget["spent_usd"]) > 1e-8
            or not isinstance(verification, dict)
            or verification.get("status") != "fail"
            or not acceptance.qualified(verification)
            or verification.get("contract_digest") != frozen.get("contract_digest")
            or not isinstance(evidence, dict)
            or evidence.get("protected_unchanged") is not True
            or evidence.get("blocked_reason")
            or not isinstance(artefacts, dict) or artefacts.get("missing")
            or not isinstance(command, dict) or command.get("exit_code") != 1
            or command.get("timed_out") is not False):
        raise CheckpointStop("first attempt is not a settled verified public failure")
    if public_runner is None:
        check = subprocess.run([sys.executable, "-B", "public_check.py"], cwd=actor,
                               capture_output=True, text=True, timeout=15, check=False)
    else:
        check = public_runner(["python3", "-B", "public_check.py"], cwd=actor,
                              capture_output=True, timeout=30, shell=False)
    stderr = check.stderr.decode() if isinstance(check.stderr, bytes) else check.stderr
    stdout = check.stdout.decode() if isinstance(check.stdout, bytes) else check.stdout
    if check.returncode != 1 or "AssertionError" not in stderr:
        raise CheckpointStop("independent public check is not a failed assertion")
    return {"schema_version": 1, "producer_root_id": state["root_id"],
            "producer_cost_usd": budget["spent_usd"],
            "producer_receipt_digest": attempt["receipt_digest"],
            "next_worker_cell": ladder[1], "successor_worker_attempts": 1,
            "public_check_exit_code": check.returncode,
            "public_check_output_sha256": digest((stdout + stderr).encode()),
            "actor_sha256": {name: digest(data) for name, data in sorted(files.items())}}


def twins(actor: Path, names: set[str], state: dict, destination: Path,
          public_runner: Callable | None = None) -> dict:
    """Create fresh, single-use S and A actor snapshots with identical bytes."""
    record = qualify(actor, names, state, public_runner)
    files = actor_files(actor, names)
    if {name: digest(data) for name, data in sorted(files.items())} != record["actor_sha256"]:
        raise CheckpointStop("actor changed after checkpoint check")
    if destination.exists() or destination.is_symlink():
        raise CheckpointStop("successor destination is already used")
    destination.mkdir(parents=True, mode=0o700)
    try:
        for arm in ("S", "A"):
            root = destination / arm
            root.mkdir(mode=0o700)
            for name, data in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            if {name: digest((root / name).read_bytes()) for name in files} != record["actor_sha256"]:
                raise CheckpointStop("successor snapshot differs")
        (destination / "snapshot.json").write_text(
            json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return record
    except Exception:
        shutil.rmtree(destination)
        raise
