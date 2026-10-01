#!/usr/bin/env python3
"""Check Q3 candidate grading against P01 baseline and clean reference."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from worker_wsl_q3_grade import grade

SEEDS = Path("/var/lib/orchestrator-worker-n4/seed")


def run(repo: Path) -> dict:
    source = repo / "test/fixtures/worker_q2_public/P01/actor"
    reference = repo / "test/fixtures/worker_q2_public/P01/reference"
    catalogue = json.loads((repo / "test/fixtures/worker_q2_public/catalogue.json")
                           .read_text(encoding="utf-8"))
    task = next(row for row in catalogue["tasks"] if row["id"] == "P01")
    with tempfile.TemporaryDirectory(prefix="q3-grade-probe-", dir=SEEDS) as raw:
        workspace = Path(raw)
        for relative in task["actor_files"]:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
        baseline = grade(repo, workspace, "P01", "failed")
        for relative in task["editable_paths"]:
            shutil.copyfile(reference / relative, workspace / relative)
        clean = grade(repo, workspace, "P01", "accepted")
    checks = {
        "baseline_hidden_fails": not baseline["hidden_acceptance"],
        "reference_hidden_passes": clean["hidden_acceptance"]
                                   and clean["public_pass"],
        "candidate_label": baseline["variant"] == clean["variant"] == "candidate",
        "oracle_read_denied": baseline["oracle_direct_read_denied"]
                              and clean["oracle_direct_read_denied"],
        "workspace_unchanged": baseline["source_workspace_unchanged"]
                               and clean["source_workspace_unchanged"],
        "zero_provider_call": baseline["provider_calls"] == clean["provider_calls"] == 0,
    }
    return {"result": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks, "provider_calls": 0, "provider_cost_usd": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.repo)
    except (OSError, ValueError, RuntimeError, StopIteration) as exc:
        print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
