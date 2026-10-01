"""Public-only checkpoint for a matched review after one accepted B0 attempt.

This development helper makes no provider call and does not select a case.
The case's source-cited risk record must already be bound to a frozen manifest.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable

import acceptance
import controller_evaluation
import model_registry
import controller_x5_first_failure as boundary


class ReviewStop(ValueError):
    """The accepted root or public risk record cannot be safely compared."""


def qualify_risk(files: dict[str, bytes], risk: dict, expected_digest: str) -> str:
    if (not isinstance(risk, dict)
            or set(risk) != {"schema_version", "eligible", "source", "source_sha256",
                             "quote", "finding", "next_check"}
            or risk["schema_version"] != 1 or risk["eligible"] is not True
            or not isinstance(expected_digest, str)
            or controller_evaluation.digest(risk) != expected_digest):
        raise ReviewStop("public risk record differs from the frozen manifest")
    source = risk["source"]
    quote = risk["quote"]
    if (not isinstance(source, str) or source not in files
            or not isinstance(quote, str) or len(quote.strip()) < 12
            or type(risk["source_sha256"]) is not str
            or boundary.digest(files[source]) != risk["source_sha256"]
            or not isinstance(risk["finding"], str)
            or len(risk["finding"].strip()) < 25
            or not isinstance(risk["next_check"], str)
            or len(risk["next_check"].strip()) < 25):
        raise ReviewStop("public risk has no stable source-cited check")
    try:
        source_text = files[source].decode("utf-8")
    except UnicodeError as exc:
        raise ReviewStop("public risk source is not text") from exc
    if source_text.count(quote) != 1:
        raise ReviewStop("public risk quote is not unique in its source")
    return expected_digest


def qualify(actor: Path, names: set[str], state: dict, risk: dict,
            expected_risk_digest: str, public_runner: Callable | None = None) -> dict:
    """Require a settled, independently public-passing one-call B0 root."""
    try:
        files = boundary.actor_files(actor, names)
    except boundary.CheckpointStop as exc:
        raise ReviewStop(str(exc)) from exc
    risk_digest = qualify_risk(files, risk, expected_risk_digest)
    attempts = state.get("attempts")
    budget = state.get("budget") or {}
    admission = state.get("admission") or {}
    ladder = state.get("ladder")
    if (not isinstance(state.get("root_id"), str) or not state["root_id"]
            or state.get("state") != "accepted" or admission.get("policy") != "B0"
            or not isinstance(ladder, list) or len(ladder) < 2
            or ladder[:2] != ["worker-sonnet-low", "worker-sonnet-low"]
            or not isinstance(attempts, list) or len(attempts) != 1
            or not isinstance(budget.get("unresolved"), list) or budget["unresolved"]
            or budget.get("breached") is not False
            or type(budget.get("spent_usd")) not in (int, float)
            or type(budget.get("limit_usd")) not in (int, float)
            or not 0 < budget["spent_usd"] <= budget["limit_usd"]):
        raise ReviewStop("not a bounded accepted one-call B0 root")
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
            or verification.get("status") != "pass"
            or not acceptance.qualified(verification)
            or verification.get("contract_digest") != frozen.get("contract_digest")
            or not isinstance(evidence, dict)
            or evidence.get("protected_unchanged") is not True
            or evidence.get("blocked_reason")
            or not isinstance(artefacts, dict) or artefacts.get("missing")
            or not isinstance(command, dict) or command.get("exit_code") != 0
            or command.get("timed_out") is not False):
        raise ReviewStop("first attempt is not a settled verified public success")
    if public_runner is None:
        check = subprocess.run([sys.executable, "-B", "public_check.py"], cwd=actor,
                               capture_output=True, text=True, timeout=15, check=False)
    else:
        check = public_runner(["python3", "-B", "public_check.py"], cwd=actor,
                              capture_output=True, timeout=30, shell=False)
    stderr = check.stderr.decode() if isinstance(check.stderr, bytes) else check.stderr
    stdout = check.stdout.decode() if isinstance(check.stdout, bytes) else check.stdout
    if check.returncode != 0:
        raise ReviewStop("independent public check no longer passes")
    return {"schema_version": 1, "producer_root_id": state["root_id"],
            "producer_cost_usd": budget["spent_usd"],
            "producer_receipt_digest": attempt["receipt_digest"],
            "risk_digest": risk_digest, "next_worker_cell": ladder[1],
            "successor_worker_attempts": 1,
            "public_check_output_sha256": boundary.digest((stdout + stderr).encode()),
            "actor_sha256": {name: boundary.digest(data)
                             for name, data in sorted(files.items())}}


def twins(actor: Path, names: set[str], state: dict, risk: dict,
          expected_risk_digest: str, destination: Path,
          public_runner: Callable | None = None) -> dict:
    """Create fresh S/A roots from identical accepted public bytes."""
    record = qualify(actor, names, state, risk, expected_risk_digest, public_runner)
    files = boundary.actor_files(actor, names)
    if {name: boundary.digest(data) for name, data in sorted(files.items())} != record["actor_sha256"]:
        raise ReviewStop("accepted actor changed after checkpoint")
    if destination.exists() or destination.is_symlink():
        raise ReviewStop("successor destination is already used")
    destination.mkdir(parents=True, mode=0o700)
    try:
        for arm in ("S", "A"):
            root = destination / arm
            root.mkdir(mode=0o700)
            for name, data in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            if {name: boundary.digest((root / name).read_bytes())
                    for name in files} != record["actor_sha256"]:
                raise ReviewStop("successor snapshot differs")
        (destination / "snapshot.json").write_text(
            json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return record
    except Exception:
        shutil.rmtree(destination)
        raise


def write_review_goals(pair: Path, risk: dict, expected_risk_digest: str,
                       edit_summary: str) -> dict:
    """Give equal accepted twins a distinct, frozen public-risk review goal."""
    snapshot_path = pair / "snapshot.json"
    if snapshot_path.is_symlink() or not snapshot_path.is_file():
        raise ReviewStop("accepted twin snapshot is unavailable")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    names = snapshot.get("actor_sha256")
    if (not isinstance(names, dict) or not names
            or snapshot.get("risk_digest") != expected_risk_digest
            or not isinstance(edit_summary, str)
            or not 1 <= len(edit_summary.strip()) <= 350
            or "\x00" in edit_summary):
        raise ReviewStop("review context differs from the accepted checkpoint")
    for arm in ("S", "A"):
        root = pair / arm
        if root.is_symlink() or not root.is_dir() or (root / "REVIEW.md").exists():
            raise ReviewStop("review goal destination is not single-use")
        files = {}
        for name, expected in names.items():
            path = root / name
            if (path.is_symlink() or not path.is_file()
                    or boundary.digest(path.read_bytes()) != expected):
                raise ReviewStop("accepted twin source changed before review")
            files[name] = path.read_bytes()
        qualify_risk(files, risk, expected_risk_digest)
    goal = ("# Review the accepted public repair\n\n"
            "The original issue's public check passes. Investigate the "
            "remaining public risk once; edit only when a discriminating "
            "check warrants it and report what you verified.\n\n"
            f"Risk: {risk['finding']}\n"
            f"Public citation: {risk['source']}: {risk['quote']}\n"
            f"Next check: {risk['next_check']}\n"
            f"Accepted edit summary:\n{edit_summary.strip()}\n")
    if len(goal) > 1000:
        raise ReviewStop("review goal exceeds the shared worker prompt bound")
    data = goal.encode("utf-8")
    for arm in ("S", "A"):
        with (pair / arm / "REVIEW.md").open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    return {"review_goal_sha256": boundary.digest(data),
            "review_goal_bytes": len(data), "source_snapshot": snapshot}
