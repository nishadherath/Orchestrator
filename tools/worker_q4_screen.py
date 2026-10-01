#!/usr/bin/env python3
"""Freeze and validate the exact Q4 M3 public information screen."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import model_registry
import worker_q4_public_calibrate as calibration
import worker_wsl_q4_attestation as q4_host
from worker_adapter import digest
from worker_q3_public_catalogue import FIXTURES, ROOT, build, sha
from worker_q3_public_source import verify as verify_upstream

TASKS = calibration.TASKS
LABELS = ("b0-a", "b0-b", "sonnet-xhigh", "opus-high")
FIRST_CELL = {"b0-a": "worker-sonnet-low", "b0-b": "worker-sonnet-low",
              "sonnet-xhigh": "worker-sonnet-xhigh",
              "opus-high": "worker-opus-high"}
REPAIR_TAIL = ["worker-sonnet-low", "worker-opus-high"]
NOTICE = ROOT / "docs/stage-results/worker-q4-m3-spend-notice-2026-09-26.md"
MANIFEST = ROOT / "test/results/2026-09-26-worker-q4-m3-manifest.json"
APPROVAL = ROOT / "test/results/2026-09-26-worker-q4-m3-approval.json"
CALIBRATION = calibration.OUTPUT
HOST = q4_host.OUTPUT
ALLOCATION = 6.0
IDENTITY_ALLOCATION = 1.0
MAX_TASK_CALLS = 48
MAX_IDENTITY_CALLS = 3
MAXIMUM_USD = 99.0
HEX = re.compile(r"[0-9a-f]{64}\Z")
SOURCES = (
    "tools/task_executor.py", "tools/worker_adapter.py",
    "tools/worker_quality_v2.py", "tools/worker_q4_adapter.py",
    "tools/worker_q4_public_calibrate.py", "tools/worker_q4_screen.py",
    "tools/worker_q4_screen_live.py", "tools/worker_wsl_q4_adapter.py",
    "tools/worker_wsl_namespace_q4.sh", "tools/worker_wsl_q4_auth_probe.py",
)


class ScreenError(RuntimeError):
    """The prospective M3 screen is not safe to admit."""


def live_rubric(task_id: str) -> tuple[dict, dict]:
    """Bind the calibrated predicate set to the live adapter task identity."""
    task, calibrated = calibration.quality_task(task_id)
    issue = (FIXTURES / task_id / "actor/ISSUE.md").read_text(encoding="utf-8")
    live_task = digest({"issue": issue,
                        "allowed_edits": task["editable_paths"]})
    rubric = {**calibrated, "task_sha256": live_task}
    calibration.validate_rubric(rubric)
    return task, rubric


def _evidence() -> tuple[dict, dict]:
    public = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    host = json.loads(HOST.read_text(encoding="utf-8"))
    if (public.get("evidence_sha256") != digest({
            key: value for key, value in public.items() if key != "evidence_sha256"})
            or public.get("provider_calls") != 0
            or public.get("provider_cost_usd") != 0
            or public.get("source_families") != list(TASKS)):
        raise ScreenError("Q4 public calibration is invalid")
    if not q4_host.validate(host, check_host=True):
        raise ScreenError("Q4 WSL host evidence is stale")
    return public, host


def rows() -> list[dict]:
    public, _ = _evidence()
    calibrated = {row["task_id"]: row for row in public["rows"]}
    material = {}
    for task_id in TASKS:
        task, rubric = live_rubric(task_id)
        frozen = json.loads((FIXTURES / task_id / "task.json").read_text(
            encoding="utf-8"))
        origin = verify_upstream(task_id)
        row = calibrated.get(task_id) or {}
        if (task != frozen or origin["source_commit"] != task["source_commit"]
                or row.get("q4_task_sha256") != calibration.quality_task(
                    task_id)[1]["task_sha256"]
                or not row.get("oracle_read_denied")
                or not row.get("report_store_read_denied")):
            raise ScreenError(f"{task_id} source or calibration changed")
        material[task_id] = (task, rubric)
    ordered = sorted(TASKS, key=lambda name: material[name][1]["task_sha256"])
    result = []
    sequence = 0
    for rank, task_id in enumerate(ordered):
        task, rubric = material[task_id]
        order = [*LABELS[rank:], *LABELS[:rank]]
        for position, label in enumerate(order, 1):
            sequence += 1
            result.append({
                "sequence": sequence, "latin_rank": rank + 1,
                "latin_position": position, "episode_label": label,
                "task_id": task_id, "source_task_sha256": task["task_sha256"],
                "task_sha256": rubric["task_sha256"], "rubric": rubric,
                "actor_files": task["actor_files"],
                "editable_paths": task["editable_paths"],
                "oracle_sha256": task["oracle_sha256"],
                "case_source_sha256": task["case_source_sha256"],
                "first_cell": FIRST_CELL[label],
                "repair_cells": REPAIR_TAIL,
                "ladder": [FIRST_CELL[label], *REPAIR_TAIL],
                "episode_maximum_usd": ALLOCATION,
            })
    return result


def build_manifest(date_utc: str, notice_sha256: str) -> dict:
    if (dt.date.fromisoformat(date_utc) != dt.datetime.now(dt.timezone.utc).date()
            or not HEX.fullmatch(notice_sha256)):
        raise ScreenError("manifest needs today's UTC date and dated notice digest")
    public, host = _evidence()
    registry = model_registry.load()
    cells = tuple(FIRST_CELL[label] for label in LABELS)
    if ([model_registry.model_class_for_provider_id(
             model_registry.resolve_cell(cell, registry)["cli_model"], registry)
         for cell in ("worker-sonnet-low", "worker-sonnet-xhigh", "worker-opus-high")]
            != ["sonnet", "sonnet", "opus"]):
        raise ScreenError("Q4 model identities changed")
    screen_rows = rows()
    value = {
        "schema_version": 1, "profile": "worker-q4-m3-public-screen",
        "date_utc": date_utc,
        "credential_method": "claude-code-wsl-subscription",
        "spend_notice_sha256": notice_sha256,
        "calibration_sha256": sha(CALIBRATION),
        "calibration_evidence_sha256": public["evidence_sha256"],
        "host_sha256": sha(HOST), "host_evidence_sha256": host["evidence_sha256"],
        "runtime_launcher_sha256": host["runtime_launcher_sha256"],
        "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
        "registry_id": registry["registry_id"], "rows": screen_rows,
        "latin_order": {"base": list(LABELS),
                        "task_order": sorted(TASKS, key=lambda name:
                                             live_rubric(name)[1]["task_sha256"]),
                        "method": "cyclic rotations by ascending live task SHA-256"},
        "cost": {"currency": "USD", "episode_allocation_usd": ALLOCATION,
                 "task_episode_allocation_usd": len(screen_rows) * ALLOCATION,
                 "identity_probe_allocation_usd": IDENTITY_ALLOCATION,
                 "maximum_identity_probes": MAX_IDENTITY_CALLS,
                 "combined_allocation_usd": MAXIMUM_USD,
                 "maximum_task_calls": MAX_TASK_CALLS,
                 "maximum_provider_calls": MAX_TASK_CALLS + MAX_IDENTITY_CALLS,
                 "api_equivalent_projection_usd": [4.0, 60.0]},
        "selection_rules": {
            "zero_candidate_critical_errors": True,
            "unsupported_completion_not_above_each_b0": True,
            "non_negative_acceptance_and_quality_vs_each_b0": True,
            "minimum_gain": "acceptance on at least one task in both comparisons or mean quality +10 in both",
            "maximum_cost_ratio_to_mean_b0": 1.5,
            "maximum_extra_usd_per_task": 1.0,
            "winner": "least cost after dominance; quality tie then sonnet-xhigh",
        },
        "reserved_repetition_rule": (
            "one iff every B0 pair agrees on acceptance, critical/reporting safety "
            "and differs by less than 10 quality points; otherwise two"),
        "stop_rules": ["Stop on uncertain or excess charge",
                       "Stop on stale host, auth, calibration or source evidence",
                       "Stop on identity mismatch, report-binding failure or protected drift",
                       "No automatic replay of a started invocation"],
        "reserved_tasks_allowed": False, "controller_allowed": False,
        "authorisation": "operator-standing-through-Q4-2026-09-25",
    }
    if (len(screen_rows) != 16
            or sum(row["episode_maximum_usd"] for row in screen_rows) != 96
            or MAXIMUM_USD != 96 + MAX_IDENTITY_CALLS * IDENTITY_ALLOCATION
            or any(row["ladder"][1:] != REPAIR_TAIL for row in screen_rows)
            or len(cells) != 4):
        raise ScreenError("M3 order or allocation is inconsistent")
    return {**value, "manifest_sha256": digest(value)}


def validate(manifest: dict, *, check_host: bool = True) -> None:
    if NOTICE.is_symlink() or sha(NOTICE) != manifest.get("spend_notice_sha256"):
        raise ScreenError("dated spend notice differs from manifest")
    if manifest != build_manifest(manifest["date_utc"], sha(NOTICE)):
        raise ScreenError("M3 manifest differs from current inputs")
    if check_host and not q4_host.validate(
            json.loads(HOST.read_text(encoding="utf-8")), check_host=True):
        raise ScreenError("Q4 host became stale")


def validate_approval(manifest: dict, approval: dict) -> None:
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_authorised_usd": MAXIMUM_USD,
                "maximum_provider_calls": MAX_TASK_CALLS + MAX_IDENTITY_CALLS,
                "spend_notice_sha256": manifest["spend_notice_sha256"],
                "credential_method": manifest["credential_method"],
                "approved_by": "operator-standing-through-Q4-2026-09-25"}
    if (not isinstance(approval, dict)
            or {key: approval.get(key) for key in expected} != expected
            or set(approval) != set(expected) | {"approved_at"}
            or not isinstance(approval.get("approved_at"), str)
            or not approval["approved_at"].strip()):
        raise ScreenError("approval is not bound to this exact M3 campaign")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--record-standing-approval", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sum((args.prepare, args.record_standing_approval, args.check)) != 1:
        parser.error("choose exactly one action")
    try:
        if args.prepare:
            if MANIFEST.exists():
                raise ScreenError("manifest already exists")
            value = build_manifest(dt.datetime.now(dt.timezone.utc).date().isoformat(),
                                   sha(NOTICE))
            MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
        else:
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            validate(value)
        if args.record_standing_approval:
            if APPROVAL.exists():
                raise ScreenError("approval record already exists")
            approval = {"schema_version": 1, "decision": "approved",
                        "manifest_sha256": value["manifest_sha256"],
                        "maximum_authorised_usd": MAXIMUM_USD,
                        "maximum_provider_calls": MAX_TASK_CALLS + MAX_IDENTITY_CALLS,
                        "spend_notice_sha256": value["spend_notice_sha256"],
                        "credential_method": value["credential_method"],
                        "approved_by": "operator-standing-through-Q4-2026-09-25",
                        "approved_at": dt.datetime.now(dt.timezone.utc).isoformat(
                            timespec="seconds")}
            APPROVAL.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
        if args.check or args.record_standing_approval:
            validate_approval(value, json.loads(APPROVAL.read_text(encoding="utf-8")))
        print(f"PASS: Q4 M3 manifest {value['manifest_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ScreenError) as exc:
        print(f"BLOCKED: Q4 M3 manifest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
