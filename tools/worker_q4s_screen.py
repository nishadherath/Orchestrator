#!/usr/bin/env python3
"""Freeze and verify the prospective Q4S canary and six-family policy screen."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import model_registry
import worker_wsl_q4s_attestation as host_attestation
from worker_adapter import digest
from worker_q3_public_catalogue import paths
from worker_q4_adapter import REPORT_INSTRUCTION
from worker_q4r_structured import report_schema
from worker_q4s_public_catalogue import ROOT, build
from worker_q4s_public_source import FIXTURES, SOURCES as FAMILIES
from worker_q4s_rubric import rubric
from worker_q4s_trigger import OUTPUT as TRIGGERS, build as build_triggers


NOTICE = ROOT / "docs/stage-results/worker-q4s-spend-notice-2026-09-26.md"
CALIBRATION = ROOT / "test/results/2026-09-26-worker-q4s-public-calibration.json"
HOST = host_attestation.OUTPUT
MANIFEST = ROOT / "test/results/2026-09-26-worker-q4s-screen-manifest.json"
CANARY = ROOT / "test/fixtures/worker_q4s_canary"
LABELS = ("b0-a", "b0-b", "sonnet-medium")
FIRST_CELL = {"b0-a": "worker-sonnet-low", "b0-b": "worker-sonnet-low",
              "sonnet-medium": "worker-sonnet-medium"}
REPAIR_TAIL = ["worker-sonnet-low", "worker-opus-high"]
SOURCES = (
    "tools/acceptance.py", "tools/model_registry.py", "tools/route.py",
    "tools/task_executor.py", "tools/worker_adapter.py", "tools/worker_quality_v2.py",
    "tools/worker_q3_public_catalogue.py", "tools/worker_q4_adapter.py",
    "tools/worker_q4r_structured.py", "tools/worker_q4s_structured.py",
    "tools/worker_q4s_admission.py", "tools/worker_q4s_public_source.py",
    "tools/worker_q4s_partial.py", "tools/worker_q4s_public_catalogue.py",
    "tools/worker_q4s_public_grade.py", "tools/worker_q4s_rubric.py",
    "tools/worker_q4s_trigger.py", "tools/worker_q4s_screen.py",
    "tools/worker_wsl_q1.py", "tools/worker_wsl_q3_adapter.py",
    "tools/worker_wsl_transport.py", "tools/worker_wsl_q4s_adapter.py",
    "tools/worker_wsl_q4s_attestation.py", "tools/worker_wsl_namespace_q4s.sh",
    "tools/worker_wsl_q4s_install.sh", "src/model_registry.json",
    "src/cost_table.json",
)
CLI = "/opt/orchestrator-worker-runtime/bin/claude"
LAUNCHER = "/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace-q4s"
SCHEMA = "/opt/orchestrator-worker-runtime/q4s-report-schema.json"


class ScreenError(RuntimeError):
    """A frozen Q4S screen input is missing, unsafe or changed."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_sha(path: str) -> str:
    if os.name == "nt":
        result = subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root",
                                 "--", "sha256sum", path], capture_output=True,
                                text=True, timeout=30, check=False)
        if result.returncode or len(result.stdout.split()) != 2:
            raise ScreenError(f"installed WSL runtime unavailable: {path}")
        return result.stdout.split()[0]
    return sha(Path(path))


def cli_version() -> str:
    command = (["wsl.exe", "-d", "kali-linux", "-u", "root", "--", CLI, "--version"]
               if os.name == "nt" else [CLI, "--version"])
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=30, check=False)
    if result.returncode or not result.stdout.strip():
        raise ScreenError("installed Claude Code CLI version unavailable")
    return result.stdout.strip()


def canary_record() -> dict:
    actor = paths(CANARY / "actor")
    reference = paths(CANARY / "reference")
    expected_actor = {"ISSUE.md", "acceptance.json", "public_check.py",
                      "canary_box/__init__.py", "canary_box/parse.py",
                      "canary_box/store.py", "canary_box/render.py"}
    contract = json.loads(actor["acceptance.json"].read_text(encoding="utf-8"))
    editable = contract["editable_paths"]
    if (contract.get("schema_version") != 1
            or contract.get("public_command") != ["python3", "-B", "public_check.py"]
            or set(actor) != expected_actor or len(editable) != 3
            or set(reference) != set(editable)
            or any(name not in actor for name in editable)
            or len(actor) > 200 or sum(path.stat().st_size for path in actor.values()) > 5_000_000):
        raise ScreenError("synthetic canary inventory is invalid")
    value = {"origin": "authored-small-synthetic-transport-only",
             "actor_files": {name: sha(path) for name, path in actor.items()},
             "reference_files": {name: sha(path) for name, path in reference.items()},
             "editable_paths": editable, "public_command": contract["public_command"],
             "excluded_from_six_family_screen": True,
             "excluded_from_reserved_corpus": True}
    return {**value, "task_sha256": digest(value)}


def screen_rows() -> list[dict]:
    trigger = {row["task_id"]: row for row in build_triggers()["rows"]}
    material = {task_id: (build(task_id), rubric(task_id)) for task_id in FAMILIES}
    for task_id, (task, _) in material.items():
        frozen = json.loads((FIXTURES / task_id / "task.json").read_text(encoding="utf-8"))
        if frozen != task:
            raise ScreenError(f"{task_id}: frozen task catalogue changed")
    order = sorted(FAMILIES, key=lambda task_id: material[task_id][0]["task_sha256"])
    rows = []
    for rank, task_id in enumerate(order):
        task, quality = material[task_id]
        labels = LABELS[rank % 3:] + LABELS[:rank % 3]
        for position, label in enumerate(labels, 1):
            first = FIRST_CELL[label]
            rows.append({
                "sequence": len(rows) + 1, "latin_rank": rank + 1,
                "latin_position": position, "task_id": task_id,
                "episode_label": label, "first_cell": first,
                "repair_cells": REPAIR_TAIL, "ladder": [first, *REPAIR_TAIL],
                "source_task_sha256": task["task_sha256"],
                "task_sha256": quality["task_sha256"], "rubric": quality,
                "actor_files": task["actor_files"],
                "editable_paths": task["editable_paths"],
                "oracle_sha256": task["oracle_sha256"],
                "case_source_sha256": task["case_source_sha256"],
                "trigger": trigger[task_id], "episode_maximum_usd": 4.0,
            })
    if len(rows) != 18 or sum(row["episode_maximum_usd"] for row in rows) != 72:
        raise ScreenError("Q4S task order or allocations differ")
    return rows


def build_manifest(date_utc: str) -> dict:
    try:
        dt.date.fromisoformat(date_utc)
    except ValueError as error:
        raise ScreenError("manifest date is invalid") from error
    if NOTICE.is_symlink() or CALIBRATION.is_symlink() or HOST.is_symlink():
        raise ScreenError("screen evidence is redirected")
    host = json.loads(HOST.read_text(encoding="utf-8"))
    if not host_attestation.validate(host, check_host=False):
        raise ScreenError("Q4S provider-free host source evidence changed")
    if (runtime_sha(LAUNCHER) != host["runtime_launcher_sha256"]
            or runtime_sha(SCHEMA) != host["runtime_schema_sha256"]):
        raise ScreenError("installed Q4S launcher or schema changed")
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    if json.loads(TRIGGERS.read_text(encoding="utf-8")) != build_triggers():
        raise ScreenError("public trigger assessment changed")
    if (calibration.get("provider_calls") != 0
            or calibration.get("provider_cost_usd") != 0
            or calibration.get("evidence_sha256") != digest({
                key: value for key, value in calibration.items()
                if key != "evidence_sha256"})
            or {row["task_id"] for row in calibration.get("rows", [])} != set(FAMILIES)):
        raise ScreenError("Q4S provider-free calibration evidence is invalid")
    for row in calibration["rows"]:
        if (row["task_sha256"] != build(row["task_id"])["task_sha256"]
                or [item["variant"] for item in row["grades"]]
                != ["baseline", "partial", "reference"]
                or any(item["quality_rubric_sha256"] != digest(rubric(row["task_id"]))
                       for item in row["grades"])
                or [item["executable_score"] for item in row["grades"]]
                != sorted(item["executable_score"] for item in row["grades"])
                or row["grades"][-1]["executable_score"] != 100):
            raise ScreenError("Q4S calibration no longer binds its task")
    registry = model_registry.load()
    for cell, expected_class in (("worker-sonnet-low", "sonnet"),
                                 ("worker-sonnet-medium", "sonnet"),
                                 ("worker-opus-high", "opus")):
        actual_class = model_registry.model_class_for_provider_id(
            model_registry.resolve_cell(cell, registry)["cli_model"], registry)
        if actual_class != expected_class:
            raise ScreenError("Q4S model mapping changed")
    rows = screen_rows()
    ordered = [row["task_id"] for row in rows if row["latin_position"] == 1]
    value = {
        "schema_version": 1, "profile": "worker-q4s-prospective-public-screen",
        "date_utc": date_utc, "credential_method": "claude-code-wsl-subscription",
        "spend_notice_sha256": sha(NOTICE),
        "public_trigger_sha256": sha(TRIGGERS),
        "calibration_sha256": sha(CALIBRATION),
        "calibration_evidence_sha256": calibration["evidence_sha256"],
        "host_sha256": sha(HOST), "host_evidence_sha256": host["evidence_sha256"],
        "runtime_cli_version": cli_version(), "runtime_cli_sha256": runtime_sha(CLI),
        "runtime_launcher_sha256": host["runtime_launcher_sha256"],
        "runtime_schema_sha256": host["runtime_schema_sha256"],
        "report_schema_sha256": digest(report_schema()),
        "prompt_contract_sha256": hashlib.sha256(REPORT_INSTRUCTION.encode()).hexdigest(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
        "registry_id": registry["registry_id"],
        "canary": {**canary_record(), "cells": ["worker-sonnet-low",
                                               "worker-sonnet-medium"],
                   "episode_maximum_usd": 3.0, "repair_cells": [],
                   "maximum_provider_calls": 2},
        "rows": rows,
        "latin_order": {"base": list(LABELS), "task_order": ordered,
                        "method": "cyclic rotations by ascending frozen task SHA-256"},
        "policy_counterfactual": {"trigger_positive": "sonnet-medium",
                                  "trigger_negative": "corresponding-b0-repetition",
                                  "negative_medium": "diagnostic-only"},
        "cost": {"currency": "USD", "canary_allocation_usd": 6.0,
                 "screen_allocation_usd": 72.0, "combined_allocation_usd": 78.0,
                 "maximum_canary_calls": 2, "maximum_screen_calls": 54,
                 "maximum_provider_calls": 56,
                 "api_equivalent_projection_usd": [6.5, 33.0]},
        "selection_rules": {
            "family_is_independent_unit": True, "zero_policy_critical_errors": True,
            "unsupported_completion_not_above_each_b0": True,
            "invalid_report_not_above_each_b0": True,
            "non_negative_acceptance_and_mean_quality_vs_each_b0": True,
            "minimum_gain": "acceptance on >=1 family against both B0 repetitions or mean quality-v2 +10 against both",
            "maximum_policy_cost_ratio_to_mean_b0": 1.5,
            "maximum_extra_usd_per_positive_family": 1.0,
            "b0_disagreement_requires_two_reserved_repetitions": True,
        },
        "stop_rules": [
            "S3 canary must pass both heads before any S4 call",
            "After each complete family, stop on positive candidate critical error",
            "Stop on uncertain or excess charge, stale source/host/auth or protected drift",
            "Stop on model identity mismatch or invalid transport; grade settled failure",
            "A terminal missing structured report is scored and never replayed",
            "No automatic replay of a started provider invocation",
        ],
        "reserved_tasks_allowed": False, "controller_allowed": False,
        "authorisation": {"paid_calls": "operator-standing-authorised",
                          "scope": "S3 two-call canary then S4 eighteen-episode public screen under this exact manifest",
                          "stage_review": "hold-before-S3"},
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
        if args.prepare:
            if MANIFEST.exists():
                raise ScreenError("refusing to overwrite frozen Q4S manifest")
            value = build_manifest(dt.datetime.now(dt.timezone.utc).date().isoformat())
            MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
        else:
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            if value != build_manifest(value["date_utc"]):
                raise ScreenError("Q4S manifest differs from current frozen inputs")
        print(f"PASS: Q4S manifest {value['manifest_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ScreenError,
            subprocess.TimeoutExpired) as error:
        print(f"BLOCKED: Q4S screen: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
