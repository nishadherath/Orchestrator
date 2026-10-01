#!/usr/bin/env python3
"""Freeze the Q4U U3 ten-episode development canary before provider outcomes."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

from worker_adapter import digest
from worker_q4r_structured import schema_argument
from worker_q4u_assess_public import build as assessment
from worker_q4u_contract import build as contract
from worker_q4u_executor import resolve
from worker_q4u_public import ROOT


OUTPUT = ROOT / "test/results/2026-09-26-worker-q4u-u3-canary-manifest.json"
NOTICE = ROOT / "docs/stage-results/worker-q4u-u3-canary-spend-notice-2026-09-26.md"
RESERVE = ROOT / "test/fixtures/worker_q4u_public/reserve_manifest_v2.json"
ALLOCATION = 4.0
SCHEDULE = (
    ("D01W", "b0"), ("F07W", "cross_component_medium"),
    ("B02W", "coverage_repair"), ("H08W", "b0"),
    ("D01W", "cross_component_medium"), ("F07W", "b0"),
    ("B02W", "b0"), ("H08W", "coverage_repair"),
    ("D01W", "coverage_repair"), ("F07W", "coverage_repair"),
)
MECHANISMS = {"D01": "dotenv-writer-parser-boundary",
              "B02": "jsonl-eof-relative-seek",
              "F07": "event-reference-encoding",
              "H08": "event-revision-tombstone"}
SOURCES = (
    "tools/acceptance.py", "tools/task_executor.py", "tools/worker_adapter.py",
    "tools/worker_q4u_assess_public.py", "tools/worker_q4u_contract.py",
    "tools/worker_q4u_coverage.py", "tools/worker_q4u_executor.py",
    "tools/worker_q4u_grade.py", "tools/worker_q4u_canary_manifest.py",
    "tools/worker_q4u_canary_live.py", "tools/worker_wsl_q4u.py",
    "tools/worker_wsl_q4u_adapter.py", "tools/worker_wsl_q4u_probe.py",
    "tools/worker_wsl_q4u_auth_probe.py", "tools/worker_wsl_namespace_q4u.sh",
    "tools/worker_wsl_q4u_install.sh", "tools/worker_wsl_q1.py",
    "tools/worker_q4s_admission.py",
)


class ManifestError(ValueError):
    """The prospective screen no longer matches its frozen public inputs."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows() -> list[dict]:
    result = []
    for sequence, (task_id, arm) in enumerate(SCHEDULE, 1):
        folder = ROOT / "test/fixtures/worker_q4u_public" / task_id
        task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
        public = assessment(task_id)
        frozen_public = json.loads((folder / "public_assessment.json").read_text(
            encoding="utf-8"))
        if public != frozen_public or public["task_sha256"] != task["task_sha256"]:
            raise ManifestError(f"Q4U assessment or task drifted: {task_id}")
        command = contract(task_id)
        capability = {"actor_root": str((folder / "actor").resolve()),
                      "enforcement_proven": False, "budget_enforced": True,
                      "supported_cells": sorted({"worker-sonnet-low",
                                                 "worker-sonnet-medium",
                                                 "worker-opus-high"})}
        class OfflinePreview:
            offline_fake = True
        selected = resolve({"schema_version": 3, "arm": arm,
                            "manifest_sha256": "0" * 64,
                            "public_assessment": public,
                            "cost_ceiling_usd": ALLOCATION},
                           capability, ALLOCATION, OfflinePreview())
        result.append({"sequence": sequence, "task_id": task_id, "arm": arm,
                       "origin": task["origin"],
                       "mechanism": MECHANISMS[task_id[:3]],
                       "task_sha256": task["task_sha256"],
                       "evaluator_zip_sha256": task["evaluator_zip_sha256"],
                       "actor_files": task["actor_files"],
                       "editable_paths": task["editable_paths"],
                       "public_assessment_sha256": public["assessment"]["assessment_sha256"],
                       "contract_sha256": digest(command),
                       "ladder": selected["ladder"],
                       "episode_maximum_usd": ALLOCATION})
    if (len(result) != 10 or len({row["mechanism"] for row in result}) != 4
            or sum(row["arm"] == "b0" for row in result) != 4
            or sum(row["arm"] == "cross_component_medium" for row in result) != 2
            or sum(row["arm"] == "coverage_repair" for row in result) != 4
            or any(row["arm"] == "cross_component_medium" and
                   row["ladder"][0] != "worker-sonnet-medium" for row in result)
            or any(row["arm"] == "coverage_repair" and
                   row["ladder"][:2] != ["worker-sonnet-low", "worker-sonnet-medium"]
                   for row in result)):
        raise ManifestError("Q4U canary selection or policy contrast is incomplete")
    return result


def build(date_utc: str, cli_sha256: str) -> dict:
    dt.date.fromisoformat(date_utc)
    if not isinstance(cli_sha256, str) or len(cli_sha256) != 64:
        raise ManifestError("installed Claude CLI digest is required")
    reserved = json.loads(RESERVE.read_text(encoding="utf-8"))
    if reserved.get("reserve_sha256") != digest({
            key: value for key, value in reserved.items()
            if key != "reserve_sha256"}):
        raise ManifestError("Q4U reserve seal differs")
    value = {"schema_version": 1,
             "profile": "worker-q4u-u3-verification-canary",
             "date_utc": date_utc, "selection_frozen_before_provider_outcomes": True,
             "qualification_authority": False,
             "qualification_limit": "Four mechanisms and single repetitions are exploratory",
             "rows": rows(), "episode_count": len(SCHEDULE),
             "maximum_provider_calls": 30,
             "episode_allocation_usd": ALLOCATION,
             "maximum_allocation_usd": len(SCHEDULE) * ALLOCATION,
             "public_assessment_provider_calls": 0,
             "public_assessment_api_equivalent_usd": 0,
             "reserve_sha256": reserved["reserve_sha256"],
             "spend_notice_sha256": sha(NOTICE),
             "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
             "runtime_cli_sha256": cli_sha256,
             "runtime_schema_sha256": hashlib.sha256(
                 (schema_argument().split("=", 1)[1] + "\n").encode()).hexdigest(),
             "transport_mode": "claude-code-json-schema-v2",
             "structured_retry_limit": 5,
             "no_started_invocation_replay": True,
             "authorisation": "operator-standing-paid-calls-approved"}
    return {**value, "manifest_sha256": digest(value)}


def validate() -> dict:
    saved = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if saved != build(saved["date_utc"], saved["runtime_cli_sha256"]):
        raise ManifestError("Q4U canary manifest differs from current sealed inputs")
    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--cli-sha256")
    args = parser.parse_args()
    try:
        if args.prepare:
            if OUTPUT.exists():
                raise ManifestError("refusing to overwrite Q4U canary manifest")
            if not args.cli_sha256:
                raise ManifestError("--cli-sha256 is required for freeze")
            value = build(dt.datetime.now(dt.timezone.utc).date().isoformat(),
                          args.cli_sha256)
            OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")
        else:
            value = validate()
        print(f"PASS: Q4U canary {value['manifest_sha256']} "
              f"({value['episode_count']} episodes, "
              f"{value['maximum_provider_calls']} calls max)")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"BLOCKED: Q4U canary manifest: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
