#!/usr/bin/env python3
"""Freeze the four disjoint Q4U reserved cases before development outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from worker_q4u_assess_public import build as assessment
from worker_q4u_contract import build as contract
from worker_q4u_controls import check as check_control
from worker_q4u_missing import check as check_missing
from worker_q4u_reserve import check as check_implementation


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "test/fixtures/worker_q4u_public/reserve_manifest_v2.json"
IDS = ("R09", "R10", "R11", "R12")
SOURCE_FILES = ("tools/worker_q4u_assess_public.py",
                "tools/worker_q4u_contract.py",
                "tools/worker_q4u_coverage.py",
                "tools/worker_q4u_reserve.py",
                "tools/worker_q4u_controls.py",
                "tools/worker_q4u_missing.py")


class ReserveManifestError(ValueError):
    """The reserved task inventory no longer matches its frozen bytes."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def build() -> dict:
    """Recompute task, public-assessment, contract and tool bindings."""
    rows = []
    for task_id in IDS:
        bound = (check_implementation(task_id) if task_id in {"R09", "R10"}
                 else check_control(task_id) if task_id == "R11"
                 else check_missing(task_id))
        public = assessment(task_id)
        command = contract(task_id)
        task = json.loads((ROOT / "test/fixtures/worker_q4u_public" / task_id /
                           "task.json").read_text(encoding="utf-8"))
        if task["split"] != "reserved" or public["task_sha256"] != bound["task_sha256"]:
            raise ReserveManifestError(f"reserved task binding differs: {task_id}")
        rows.append({"task_id": task_id, "mechanism": task["mechanism"],
                     "task_sha256": bound["task_sha256"],
                     "evaluator_zip_sha256": bound["evaluator_zip_sha256"],
                     "public_assessment_sha256": public["assessment"]["assessment_sha256"],
                     "command_contract_sha256": digest(command)})
    mechanisms = {row["mechanism"] for row in rows}
    if len(mechanisms) != len(IDS):
        raise ReserveManifestError("reserve mechanisms are not distinct")
    value = {"schema_version": 1, "stage": "Q4U-U3-v2",
             "split": "reserved", "selection_frozen_before_provider_outcomes": True,
             "qualification_authority": False,
             "qualification_limit": "Four independent mechanisms are exploratory only",
             "rows": rows,
             "source_sha256": {name: sha((ROOT / name).read_bytes())
                               for name in SOURCE_FILES}}
    return {**value, "reserve_sha256": digest(value)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        value = build()
        if args.prepare:
            if OUTPUT.exists():
                raise ReserveManifestError(f"refusing to overwrite: {OUTPUT}")
            OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")
        elif json.loads(OUTPUT.read_text(encoding="utf-8")) != value:
            raise ReserveManifestError("reserved manifest differs from frozen inputs")
        print(f"PASS: Q4U reserve {value['reserve_sha256']} ({len(IDS)} mechanisms)")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"BLOCKED: Q4U reserve manifest: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
