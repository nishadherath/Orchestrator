#!/usr/bin/env python3
"""Q4S preflight, no-replay journal and settled stopped-patch classification.

S1 has no corpus or paid manifest. These evaluation-only boundaries are used
by the later screen once its independent task catalogue has been frozen.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Callable

from worker_adapter import digest

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class Q4SAdmissionError(RuntimeError):
    """The prospective screen cannot safely admit or settle an episode."""


def _write(path: Path, value: dict) -> None:
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    value = {**body, "state_sha256": digest(body)}
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    if value.get("state_sha256") != digest(body):
        raise Q4SAdmissionError("Q4S journal digest mismatch")
    return value


def start_campaign(path: Path, manifest_sha256: str,
                   preflight: Callable[[], dict]) -> dict:
    """Run attested auth and source checks before creating any campaign state."""
    if path.exists() or path.is_symlink():
        raise Q4SAdmissionError("campaign path already exists; no automatic replay")
    if not isinstance(manifest_sha256, str) or not _SHA256.fullmatch(manifest_sha256):
        raise Q4SAdmissionError("manifest digest is invalid")
    proof = preflight()
    if (not isinstance(proof, dict) or proof.get("result") != "PASS"
            or not isinstance(proof.get("source_sha256"), dict)
            or not proof["source_sha256"]
            or any(not isinstance(value, str) or not _SHA256.fullmatch(value)
                   for value in proof["source_sha256"].values())
            or not isinstance(proof.get("evidence_sha256"), str)
            or not _SHA256.fullmatch(proof["evidence_sha256"])
            or proof["evidence_sha256"] != digest({
                key: value for key, value in proof.items()
                if key != "evidence_sha256"})
            or (proof.get("auth") or {}).get("result") != "PASS"
            or (proof.get("auth") or {}).get("provider_calls") != 0
            or (proof.get("auth") or {}).get("provider_cost_usd") != 0
            or (proof.get("probe") or {}).get("result") != "PASS"
            or (proof.get("probe") or {}).get("provider_calls") != 0
            or (proof.get("probe") or {}).get("provider_cost_usd") != 0):
        raise Q4SAdmissionError("Q4S preflight is incomplete or not provider-free")
    path.mkdir(mode=0o700, parents=False)
    state = {"schema_version": 1, "manifest_sha256": manifest_sha256,
             "preflight_evidence_sha256": proof["evidence_sha256"],
             "status": "running", "rows": [], "total_cost_usd": 0.0,
             "total_provider_calls": 0}
    _write(path / "campaign.json", state)
    return _read(path / "campaign.json")


def mark_intent(path: Path, sequence: int, task_id: str,
                episode_label: str) -> dict:
    """Persist a unique provider-call intent before invoking an episode."""
    state_path = path / "campaign.json"
    state = _read(state_path)
    rows = state["rows"]
    if (state["status"] != "running" or type(sequence) is not int
            or sequence != len(rows) + 1 or not task_id or not episode_label
            or any(row["state"] == "provider-call-may-start" for row in rows)):
        raise Q4SAdmissionError("episode cannot be dispatched or replayed")
    rows.append({"sequence": sequence, "task_id": task_id,
                 "episode_label": episode_label,
                 "state": "provider-call-may-start"})
    _write(state_path, state)
    return _read(state_path)


def settle_episode(path: Path, episode: dict) -> dict:
    """Charge one already-graded terminal episode; never redispatch it."""
    state_path = path / "campaign.json"
    state = _read(state_path)
    rows = state["rows"]
    if not rows or rows[-1]["state"] != "provider-call-may-start":
        raise Q4SAdmissionError("no outstanding provider-call intent")
    intent = rows[-1]
    settlement = episode.get("settlement") or {}
    amount = settlement.get("charged_usd")
    calls = settlement.get("provider_calls")
    if (episode.get("task_id") != intent["task_id"]
            or episode.get("episode_label") != intent["episode_label"]
            or settlement.get("writer_stopped") is not True
            or settlement.get("cost_settled") is not True
            or type(amount) not in (int, float) or not math.isfinite(amount)
            or amount < 0 or type(calls) is not int or not 1 <= calls <= 3
            or not isinstance(episode.get("snapshot"), dict)
            or not isinstance(episode.get("executable_grade"), dict)
            or not isinstance(episode.get("quality_v2"), dict)):
        raise Q4SAdmissionError("terminal episode evidence is incomplete")
    intent.update(state="graded" if episode.get("qualification_eligible") else "terminal-failed",
                  episode=episode)
    state["total_cost_usd"] += amount
    state["total_provider_calls"] += calls
    if intent["state"] == "terminal-failed":
        state.update(status="blocked", stop_reason="scored terminal failure")
    _write(state_path, state)
    return _read(state_path)


def settle_stopped_patch(outcome: dict, workspace: Path,
                         protected_sha256: dict[str, str],
                         grade: Callable[[Path, str, dict], tuple[dict, dict]],
                         preserve: Callable[[Path], dict]) -> dict:
    """Grade a settled failure, including a missing structured report.

    The callback functions are evaluator-only. They run after source and
    accounting checks; the actor remains untouched if any check fails.
    """
    attempts = outcome.get("attempts")
    budget = outcome.get("budget") or {}
    if (outcome.get("state") not in {"accepted", "partial", "failed", "blocked"}
            or not isinstance(attempts, list) or not 1 <= len(attempts) <= 3
            or budget.get("unresolved")
            or type(budget.get("spent_usd")) not in (int, float)
            or not math.isfinite(budget["spent_usd"])
            or budget["spent_usd"] < 0):
        raise Q4SAdmissionError("root or budget has not settled")
    costs = []
    for attempt in attempts:
        receipt = attempt.get("receipt") or {}
        cost = receipt.get("cost_usd")
        if (receipt.get("terminal") is not True
                or receipt.get("writer_stopped") is not True
                or type(cost) not in (int, float) or not math.isfinite(cost)
                or cost < 0 or receipt.get("timed_out") is True):
            raise Q4SAdmissionError("attempt cost or writer remains uncertain")
        costs.append(cost)
        ledger = (budget.get("invocations") or {}).get(attempt.get("invocation_id"), {})
        ledger_cost = ledger.get("cost_usd")
        if (ledger.get("state") != "settled"
                or type(ledger_cost) not in (int, float)
                or not math.isfinite(ledger_cost)
                or not math.isclose(ledger_cost, cost, abs_tol=1e-8)):
            raise Q4SAdmissionError("attempt charge differs from settled ledger")
    if not math.isclose(sum(costs), budget["spent_usd"], abs_tol=1e-8):
        raise Q4SAdmissionError("episode charge differs from settled attempts")
    if not isinstance(protected_sha256, dict) or not protected_sha256:
        raise Q4SAdmissionError("protected source inventory is missing")
    for relative, expected in protected_sha256.items():
        source = workspace / relative
        if (not isinstance(expected, str) or not _SHA256.fullmatch(expected)
                or source.is_symlink() or not source.is_file()
                or not source.resolve().is_relative_to(workspace.resolve())
                or hashlib.sha256(source.read_bytes()).hexdigest() != expected):
            raise Q4SAdmissionError("protected source drifted")
    last = attempts[-1]["receipt"]
    report = last.get("evaluation_report") or {}
    if last.get("evaluation_report_digest") != digest(report):
        raise Q4SAdmissionError("report evidence digest mismatch")
    executable, quality = grade(workspace, outcome["state"], report)
    snapshot = preserve(workspace)
    eligible = outcome["state"] != "blocked" and all(
                   (attempt["receipt"].get("status") == "completed"
                    and attempt["receipt"].get("identity_valid") is True
                    and (attempt["receipt"].get("evaluation_report") or {}).get(
                        "observability") == "present")
                   for attempt in attempts)
    return {"settlement": {"charged_usd": budget["spent_usd"],
                           "provider_calls": len(attempts),
                           "writer_stopped": True, "cost_settled": True},
            "qualification_eligible": eligible,
            "report_observability": report.get("observability"),
            "executable_grade": executable, "quality_v2": quality,
            "snapshot": snapshot,
            "protected_sha256": protected_sha256}
