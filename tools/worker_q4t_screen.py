#!/usr/bin/env python3
"""Freeze the non-replayed Q4T six-family corpus and policy screen design."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import model_registry
from worker_adapter import digest
from worker_q4r_structured import report_schema
from worker_q4t_public import FAMILIES, ROOT, UPSTREAM, actor_root, build, rubric, sha, triggers
from worker_q4t_public_grade import OUTPUT as T07_CALIBRATION, build_evidence
from worker_q4t_structured import STRUCTURED_RETRIES
from worker_quality_v2 import validate_rubric


MANIFEST = ROOT / "test/results/2026-09-26-worker-q4t-s2-manifest.json"
NOTICE = ROOT / "docs/stage-results/worker-q4t-s2-spend-notice-2026-09-26.md"
Q4S_PARENT = ROOT / "test/results/2026-09-26-worker-q4s-screen-manifest.json"
Q4S_CALIBRATION = ROOT / "test/results/2026-09-26-worker-q4s-public-calibration.json"
C1_MANIFEST = ROOT / "test/results/2026-09-26-worker-q4t-c1-manifest.json"
LABELS = ("b0-a", "b0-b", "sonnet-medium")
FIRST_CELL = {"b0-a": "worker-sonnet-low", "b0-b": "worker-sonnet-low",
              "sonnet-medium": "worker-sonnet-medium"}
REPAIR_TAIL = ["worker-sonnet-low", "worker-opus-high"]
SOURCE_FILES = (
    "tools/worker_q4t_public.py", "tools/worker_q4t_public_grade.py",
    "tools/worker_q4t_screen.py", "tools/worker_q4t_policy.py",
    "tools/worker_q4t_structured.py", "tools/worker_wsl_q4t_adapter.py",
    "tools/worker_wsl_namespace_q4t.sh", "tools/worker_q4s_admission.py",
    "tools/worker_q4s_public_catalogue.py", "tools/worker_q4s_public_grade.py",
    "tools/worker_q4s_rubric.py", "tools/worker_q4s_trigger.py",
    "tools/worker_quality_v2.py", "tools/task_executor.py",
    "tools/worker_adapter.py", "tools/worker_wsl_q3_adapter.py",
    "tools/model_registry.py", "src/model_registry.json", "src/cost_table.json",
)
PRIOR_S4_STATE_SHA256 = "963e7c1849b1b097c1b3cdd897a637a7cfed273d6fb960ecdd5162dec0eee11f"
PRIOR_S4_TASKS = ("S03",)


class ScreenError(RuntimeError):
    """The Q4T corpus or frozen candidate design is unsafe."""


def live_rubric(row: dict) -> dict:
    value = dict(row["rubric"])
    issue = (actor_root(row["task_id"]) / "ISSUE.md").read_text(encoding="utf-8")
    value["task_sha256"] = digest({"issue": issue,
                                   "allowed_edits": tuple(row["editable_paths"])})
    return validate_rubric(value)


def screen_rows() -> list[dict]:
    assessments = triggers()
    material = {task_id: (build(task_id), rubric(task_id)) for task_id in FAMILIES}
    if (len(material) != 6 or sum(row["triggered"] for row in assessments.values()) != 4
            or set(UPSTREAM) & set(PRIOR_S4_TASKS)
            or assessments["T07"]["triggered"] is not True):
        raise ScreenError("Q4T corpus or trigger balance is invalid")
    order = sorted(FAMILIES, key=lambda name: material[name][0]["task_sha256"])
    rows = []
    for rank, task_id in enumerate(order):
        task, quality = material[task_id]
        labels = LABELS[rank % 3:] + LABELS[:rank % 3]
        for position, label in enumerate(labels, 1):
            first = FIRST_CELL[label]
            rows.append({
                "sequence": len(rows) + 1, "latin_rank": rank + 1,
                "latin_position": position, "task_id": task_id,
                "origin": task.get("origin", "pinned-upstream-regression"),
                "episode_label": label, "first_cell": first,
                "repair_cells": REPAIR_TAIL, "ladder": [first, *REPAIR_TAIL],
                "source_task_sha256": task["task_sha256"],
                "task_sha256": quality["task_sha256"], "rubric": quality,
                "actor_files": task["actor_files"],
                "editable_paths": task["editable_paths"],
                "oracle_sha256": task["oracle_sha256"],
                "case_source_sha256": task["case_source_sha256"],
                "trigger": assessments[task_id], "episode_maximum_usd": 4.0,
            })
    if len(rows) != 18:
        raise ScreenError("Q4T balanced arm inventory is incomplete")
    return rows


def build_manifest(date_utc: str) -> dict:
    dt.date.fromisoformat(date_utc)
    parent = json.loads(Q4S_PARENT.read_text(encoding="utf-8"))
    prior_calibration = json.loads(Q4S_CALIBRATION.read_text(encoding="utf-8"))
    c1 = json.loads(C1_MANIFEST.read_text(encoding="utf-8"))
    t07 = json.loads(T07_CALIBRATION.read_text(encoding="utf-8"))
    if (parent.get("manifest_sha256") != digest({
            key: value for key, value in parent.items() if key != "manifest_sha256"})
            or c1.get("manifest_sha256") != digest({
                key: value for key, value in c1.items() if key != "manifest_sha256"})
            or c1.get("transport_mode") != "claude-code-json-schema-v2"
            or c1.get("structured_retry_limit") != STRUCTURED_RETRIES
            or t07 != build_evidence()
            or prior_calibration.get("evidence_sha256") != digest({
                key: value for key, value in prior_calibration.items()
                if key != "evidence_sha256"})
            or {row["task_id"] for row in prior_calibration["rows"]}
               < set(UPSTREAM)):
        raise ScreenError("prior freeze, canary or T07 calibration differs")
    for cell, expected in (("worker-sonnet-low", "claude-sonnet-5"),
                           ("worker-sonnet-medium", "claude-sonnet-5"),
                           ("worker-opus-high", "claude-opus-5")):
        if model_registry.resolve_cell(cell)["cli_model"] != expected:
            raise ScreenError(f"model registry mapping changed for {cell}")
    rows = screen_rows()
    value = {
        "schema_version": 1, "profile": "worker-q4t-s2-six-family-design",
        "date_utc": date_utc,
        "credential_method": "claude-code-wsl-subscription",
        "q4s_parent_manifest_sha256": parent["manifest_sha256"],
        "q4s_prior_campaign_state_sha256": PRIOR_S4_STATE_SHA256,
        "q4s_prior_paid_task_ids": list(PRIOR_S4_TASKS),
        "c1_manifest_sha256": c1["manifest_sha256"],
        "c1_campaign_state_sha256":
            "f582b910d6f5759687fbad2fa6e7cbd980b358750c39981eb0d499707e08949e",
        "q4s_calibration_sha256": sha(Q4S_CALIBRATION),
        "t07_calibration_sha256": sha(T07_CALIBRATION),
        "spend_notice_sha256": sha(NOTICE),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_FILES},
        "report_schema_sha256": digest(report_schema()),
        "transport_mode": "claude-code-json-schema-v2",
        "structured_retry_limit": STRUCTURED_RETRIES,
        "runtime_cli_version": parent["runtime_cli_version"],
        "runtime_cli_sha256": parent["runtime_cli_sha256"],
        "runtime_launcher_sha256": c1["installed_launcher_sha256"],
        "runtime_schema_sha256": parent["runtime_schema_sha256"],
        "rows": rows,
        "live_rubric_sha256": {name: digest(live_rubric(next(
            row for row in rows if row["task_id"] == name))) for name in FAMILIES},
        "latin_order": {"base": list(LABELS),
                        "task_order": [row["task_id"] for row in rows
                                       if row["latin_position"] == 1],
                        "method": "cyclic rotations by ascending frozen task SHA-256"},
        "policy_counterfactual": {"trigger_positive": "sonnet-medium",
                                  "trigger_negative": "corresponding-b0-repetition",
                                  "negative_medium": "diagnostic-only"},
        "selection_rules": parent["selection_rules"],
        "stop_policy": {"source": "tools/worker_q4t_policy.py",
                        "settled_report_failure": "score-with-zero-report-credit",
                        "unsettled_or_unknown_failure": "stop",
                        "positive_candidate_critical": "stop",
                        "no_started_invocation_replay": True},
        "cost": {"episode_allocation_usd": 4.0,
                 "maximum_allocation_usd": 72.0,
                 "maximum_provider_calls": 54,
                 "api_equivalent_projection_usd": [5.0, 40.0]},
        "reserved_tasks_allowed": False, "controller_allowed": False,
        "authorisation": {"paid_calls": "operator-standing-authorised",
                          "scope": "Q4T 18-episode screen after separate paid-driver freeze",
                          "stage_review": "hold-after-S2-before-paid-driver"},
    }
    return {**value, "manifest_sha256": digest(value)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.prepare == args.check:
        parser.error("choose exactly one of --prepare or --check")
    try:
        value = build_manifest(dt.datetime.now(dt.timezone.utc).date().isoformat()
                               if args.prepare else json.loads(
                                   MANIFEST.read_text(encoding="utf-8"))["date_utc"])
        if args.prepare:
            if MANIFEST.exists() or MANIFEST.is_symlink():
                raise ScreenError("refusing to overwrite Q4T S2 manifest")
            MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
        elif json.loads(MANIFEST.read_text(encoding="utf-8")) != value:
            raise ScreenError("Q4T S2 manifest differs from current source")
        print(f"PASS: Q4T S2 {value['manifest_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f"BLOCKED: Q4T S2: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
