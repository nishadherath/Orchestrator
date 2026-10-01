#!/usr/bin/env python3
"""Freeze the Q4S trigger from public issues and editable source only."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from worker_q4s_public_source import FIXTURES, SOURCES


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs/WORKER-Q4S-PUBLIC-TRIGGERS-2026-09-26.json"
MECHANISMS = {
    "S01": (True, "Callable detection, generated assignment and field hooks must preserve one-yield before/after assignment semantics."),
    "S02": (True, "Hookspec defaults, plugin validation and dispatch must pass the same effective argument through direct and historic calls."),
    "S03": (True, "Header storage, automatic framing and wire serialisation must preserve raw casing while matching names case-insensitively."),
    "S04": (True, "List, keyed list, dictionary and set reducers must reconstruct values and key behaviour without private indexes."),
    "S05": (False, "The zero-cache seekable lookahead implementation must bound retained state during repeated peeks."),
    "S06": (False, "The core joiner validation error path must retain the specific invalid-context exception while preserving unknown-data errors."),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    rows = []
    for task_id, (_, _, _, _, package, _, _, names) in SOURCES.items():
        triggered, mechanism = MECHANISMS[task_id]
        actor = FIXTURES / task_id / "actor"
        issue = actor / "ISSUE.md"
        issue_text = issue.read_text(encoding="utf-8")
        modules = [f"{package}/{name}" for name in names]
        if (len(modules) < 3 if triggered else len(modules) > 2):
            raise ValueError(f"{task_id}: trigger scope conflicts with edit inventory")
        if not all(name in issue_text for name in modules):
            raise ValueError(f"{task_id}: public issue omits an editable source path")
        if not triggered and "no cross-component" not in issue_text:
            raise ValueError(f"{task_id}: negative public issue has no boundary statement")
        rows.append({
            "task_id": task_id, "triggered": triggered, "mechanism": mechanism,
            "issue_citation": f"test/fixtures/worker_q4s_public/{task_id}/actor/ISSUE.md:3",
            "issue_sha256": sha(issue), "modules": modules,
            "source_sha256": {name: sha(actor / name) for name in modules},
        })
    if sum(row["triggered"] for row in rows) != 4:
        raise ValueError("Q4S trigger inventory must contain four positives")
    return {"schema_version": 1,
            "assessment_method": "operator-authored-public-issue-and-source-only",
            "prior_model_outputs_used": False,
            "protected_oracle_or_reference_used": False, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.prepare == args.check:
        parser.error("choose exactly one of --prepare or --check")
    try:
        value = build()
        if args.prepare:
            if OUTPUT.exists():
                raise ValueError("refusing to overwrite frozen trigger assessment")
            OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")
        elif json.loads(OUTPUT.read_text(encoding="utf-8")) != value:
            raise ValueError("trigger assessment or public evidence changed")
        print("PASS: Q4S four positive and two negative public triggers")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"BLOCKED: Q4S trigger: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
