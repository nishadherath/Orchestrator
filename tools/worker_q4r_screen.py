#!/usr/bin/env python3
"""Freeze a prospective schema-bound Sonnet-high public comparison."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import model_registry
import worker_q4_screen as q4
import worker_wsl_q4r_attestation as host_attestation
from worker_adapter import digest
from worker_q3_public_catalogue import FIXTURES, ROOT, sha
from worker_q4r_structured import report_schema

TASKS = q4.TASKS
LABELS = ("b0-a", "b0-b", "sonnet-high")
FIRST_CELL = {"b0-a": "worker-sonnet-low", "b0-b": "worker-sonnet-low",
              "sonnet-high": "worker-sonnet-high"}
REPAIR_TAIL = ["worker-sonnet-low", "worker-opus-high"]
TRIGGERS = ROOT / "docs/WORKER-Q4R-PUBLIC-TRIGGERS-2026-09-26.json"
NOTICE = ROOT / "docs/stage-results/worker-q4r-r1-spend-notice-2026-09-26.md"
MANIFEST = ROOT / "test/results/2026-09-25-worker-q4r-r1-manifest.json"
APPROVAL = ROOT / "test/results/2026-09-25-worker-q4r-r1-approval.json"
HOST = host_attestation.OUTPUT
CALIBRATION = q4.CALIBRATION
ALLOCATION = 6.0
MAX_TASK_CALLS = 36
MAXIMUM_USD = 72.0
HEX = re.compile(r"[0-9a-f]{64}\Z")
SOURCES = (
    "tools/acceptance.py", "tools/model_registry.py", "tools/route.py",
    "tools/task_executor.py", "tools/worker_adapter.py",
    "tools/worker_selector.py", "tools/worker_wsl_q1.py",
    "tools/worker_wsl_transport.py", "tools/worker_wsl_q3_adapter.py",
    "tools/worker_wsl_q3_public.py", "tools/worker_q3_public_catalogue.py",
    "tools/worker_quality_v2.py", "tools/worker_q4_adapter.py",
    "tools/worker_q4r_structured.py", "tools/worker_q4_screen.py",
    "tools/worker_q4r_screen.py", "tools/worker_q4r_screen_live.py",
    "tools/worker_wsl_q4r_adapter.py", "tools/worker_wsl_namespace_q4r.sh",
    "tools/worker_wsl_q4r_install.sh", "tools/worker_wsl_q4r_attestation.py",
)


class ScreenError(RuntimeError):
    """The Q4R public comparison is not safe to admit."""


def trigger_rows() -> dict[str, dict]:
    value = json.loads(TRIGGERS.read_text(encoding="utf-8"))
    if (value.get("schema_version") != 1
            or value.get("assessment_method") != "operator-authored-public-issue-only"
            or len(value.get("rows", [])) != len(TASKS)):
        raise ScreenError("Q4R public trigger assessment is incomplete")
    result = {}
    for row in value["rows"]:
        task_id = row["task_id"]
        issue = FIXTURES / task_id / "actor/ISSUE.md"
        task, _ = q4.live_rubric(task_id)
        if (task_id not in TASKS or task_id in result
                or row["triggered"] is not True
                or row["issue_sha256"] != sha(issue)
                or len(row["modules"]) < 3
                or not set(row["modules"]) <= set(task["editable_paths"])
                or row["citation"] != f"test/fixtures/worker_q3_public/{task_id}/actor/ISSUE.md:2"
                or not isinstance(row["mechanism"], str) or not row["mechanism"]):
            raise ScreenError(f"Q4R trigger evidence changed: {task_id}")
        result[task_id] = row
    if set(result) != set(TASKS):
        raise ScreenError("Q4R public trigger set differs from calibrated tasks")
    return result


def rows() -> list[dict]:
    triggers = trigger_rows()
    # Reuse only the immutable source/rubric binding from Q4, never its model
    # outputs, grade or arm order. Every Q4R episode has a fresh workspace.
    source = {row["task_id"]: row for row in q4.rows()
              if row["episode_label"] == "b0-a"}
    if set(source) != set(TASKS):
        raise ScreenError("Q4 public task binding is incomplete")
    ordered = sorted(TASKS, key=lambda task_id: source[task_id]["task_sha256"])
    result = []
    for rank, task_id in enumerate(ordered):
        order = [*LABELS[rank % len(LABELS):],
                 *LABELS[:rank % len(LABELS)]]
        for position, label in enumerate(order, 1):
            base = source[task_id]
            first = FIRST_CELL[label]
            result.append({
                "sequence": len(result) + 1, "latin_rank": rank + 1,
                "latin_position": position, "episode_label": label,
                "task_id": task_id, "source_task_sha256": base["source_task_sha256"],
                "task_sha256": base["task_sha256"], "rubric": base["rubric"],
                "actor_files": base["actor_files"],
                "editable_paths": base["editable_paths"],
                "oracle_sha256": base["oracle_sha256"],
                "case_source_sha256": base["case_source_sha256"],
                "trigger": triggers[task_id], "first_cell": first,
                "repair_cells": REPAIR_TAIL,
                "ladder": [first, *REPAIR_TAIL],
                "episode_maximum_usd": ALLOCATION,
            })
    return result


def build_manifest(date_utc: str, notice_sha256: str) -> dict:
    if not HEX.fullmatch(notice_sha256):
        raise ScreenError("Q4R notice digest is invalid")
    try:
        dt.date.fromisoformat(date_utc)
    except ValueError as exc:
        raise ScreenError("Q4R UTC date is invalid") from exc
    host = json.loads(HOST.read_text(encoding="utf-8"))
    if not host_attestation.validate(host, check_host=True):
        raise ScreenError("Q4R WSL host evidence is stale")
    registry = model_registry.load()
    if (registry["registry_id"] != "claude-cells-v1"
            or model_registry.resolve_cell("worker-sonnet-high")["cli_model"]
            != "claude-sonnet-5"):
        raise ScreenError("Q4R model identity changed")
    screen_rows = rows()
    if len(screen_rows) != 12 or sum(row["episode_maximum_usd"]
                                      for row in screen_rows) != MAXIMUM_USD:
        raise ScreenError("Q4R schedule or allocation differs")
    value = {
        "schema_version": 1, "profile": "worker-q4r-r1-public-screen",
        "date_utc": date_utc, "credential_method": "claude-code-wsl-subscription",
        "spend_notice_sha256": notice_sha256,
        "public_trigger_sha256": sha(TRIGGERS),
        "calibration_sha256": sha(CALIBRATION),
        "host_sha256": sha(HOST), "host_evidence_sha256": host["evidence_sha256"],
        "runtime_launcher_sha256": host["runtime_launcher_sha256"],
        "runtime_schema_sha256": host["runtime_schema_sha256"],
        "schema_sha256": digest(report_schema()),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
        "registry_id": registry["registry_id"], "rows": screen_rows,
        "latin_order": {"base": list(LABELS), "task_order": sorted(
            TASKS, key=lambda name: q4.live_rubric(name)[1]["task_sha256"]),
            "method": "cyclic rotations by ascending live task SHA-256"},
        "cost": {"currency": "USD", "episode_allocation_usd": ALLOCATION,
                 "combined_allocation_usd": MAXIMUM_USD,
                 "maximum_task_calls": MAX_TASK_CALLS,
                 "maximum_provider_calls": MAX_TASK_CALLS,
                 "api_equivalent_projection_usd": [4.0, 25.0]},
        "selection_rules": {
            "zero_candidate_critical_errors": True,
            "unsupported_completion_not_above_each_b0": True,
            "non_negative_acceptance_and_quality_vs_each_b0": True,
            "minimum_gain": "acceptance on at least one task in both comparisons or mean quality +10 in both",
            "maximum_cost_ratio_to_mean_b0": 1.5,
            "maximum_extra_usd_per_triggered_task": 1.0,
        },
        "stop_rules": ["Stop on uncertain or excess charge",
                       "Stop on stale host, auth, calibration or source evidence",
                       "Stop on identity mismatch, transport-invalid report or protected drift",
                       "No automatic replay of a started invocation"],
        "reserved_tasks_allowed": False, "controller_allowed": False,
        "authorisation": "exact-operator-approval-required",
    }
    return {**value, "manifest_sha256": digest(value)}


def validate(manifest: dict, *, check_host: bool = True) -> None:
    if NOTICE.is_symlink() or sha(NOTICE) != manifest.get("spend_notice_sha256"):
        raise ScreenError("Q4R spend notice differs from manifest")
    if manifest != build_manifest(manifest["date_utc"], sha(NOTICE)):
        raise ScreenError("Q4R manifest differs from current inputs")
    if check_host and not host_attestation.validate(
            json.loads(HOST.read_text(encoding="utf-8")), check_host=True):
        raise ScreenError("Q4R host became stale")


def validate_approval(manifest: dict, approval: dict) -> None:
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_authorised_usd": MAXIMUM_USD,
                "maximum_provider_calls": MAX_TASK_CALLS,
                "spend_notice_sha256": manifest["spend_notice_sha256"],
                "credential_method": manifest["credential_method"],
                "approved_by": "operator"}
    if (not isinstance(approval, dict)
            or {key: approval.get(key) for key in expected} != expected
            or set(approval) != set(expected) | {"approved_at"}
            or not isinstance(approval.get("approved_at"), str)
            or not approval["approved_at"].strip()):
        raise ScreenError("approval is not bound to this exact Q4R campaign")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare:
            today = dt.datetime.now(dt.timezone.utc).date().isoformat()
            manifest = build_manifest(today, sha(NOTICE))
            if MANIFEST.exists():
                raise ScreenError("Q4R manifest already exists; no overwrite")
            MANIFEST.write_text(json.dumps(manifest, indent=2,
                                           sort_keys=True) + "\n", encoding="utf-8")
            print(manifest["manifest_sha256"])
        elif args.check:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            validate(manifest)
            print("PASS: Q4R manifest current")
        else:
            parser.error("choose --prepare or --check")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ScreenError) as exc:
        print(f"BLOCKED: Q4R manifest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
