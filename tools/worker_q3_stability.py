#!/usr/bin/env python3
"""Repeat the completed Q3 public grades without another provider call."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

from worker_adapter import digest as record_digest
from worker_wsl_q2_verify import verify
from worker_wsl_q3_grade import grade

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "test/results/2026-09-25-worker-q3-canary-run/campaign.json"
OUTPUT = ROOT / "test/results/2026-09-25-worker-q3-stability.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(repeats: int) -> dict:
    if os.geteuid() != 0 or repeats < 2 or repeats > 20:
        raise ValueError("WSL root and a repeat count from 2 to 20 are required")
    campaign = json.loads(RUN.read_text(encoding="utf-8"))
    if campaign.get("state_sha256") != record_digest({
            key: value for key, value in campaign.items()
            if key != "state_sha256"}):
        raise ValueError("the Q3 canary checkpoint digest is invalid")
    if (campaign.get("status") != "complete"
            or [row.get("task_id") for row in campaign.get("rows", [])]
            != ["P01", "P02"]):
        raise ValueError("the two-task Q3 canary is not complete")
    row = campaign["rows"][0]
    workspace = Path(row["episode"]["workspace"])
    source = ROOT / "test/fixtures/worker_q2_public/P01/actor"
    oracle = ROOT / "test/oracles/worker_q2_public/P01.json"
    catalogue = json.loads((source.parent.parent / "catalogue.json").read_text(
        encoding="utf-8"))
    task = next(task for task in catalogue["tasks"] if task["id"] == "P01")
    before = {name: digest(workspace / name) for name in task["actor_files"]}
    baseline = []
    candidate = []
    for _ in range(repeats):
        for target, result in (
            (baseline, verify("P01", source, None, oracle, "failed", "baseline")),
            (candidate, grade(ROOT, workspace, "P01", row["episode"]["root_state"])),
        ):
            target.append({"public_pass": result["public_pass"],
                           "hidden_acceptance": result["hidden_acceptance"],
                           "quality": result["quality"],
                           "cases": {case["milestone"]: case["passed"]
                                     for case in result["cases"]}})
    after = {name: digest(workspace / name) for name in task["actor_files"]}
    expected = row["episode"]["hidden_grade"]
    stable_candidate = all(
        item["public_pass"] == expected["public_pass"]
        and item["hidden_acceptance"] == expected["hidden_acceptance"]
        and item["quality"] == expected["quality"]
        and item["cases"] == {case["milestone"]: case["passed"]
                              for case in expected["cases"]}
        for item in candidate)
    stable_baseline = all(item == baseline[0] for item in baseline)
    value = {"schema_version": 1,
             "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(
                 timespec="seconds"),
             "campaign_sha256": digest(RUN),
             "manifest_sha256": campaign["manifest_sha256"],
             "source_sha256": {name: digest(ROOT / name) for name in (
                 "tools/worker_q3_stability.py",
                 "tools/worker_wsl_q3_grade.py",
                 "tools/worker_wsl_q2_verify.py")},
             "repeats": repeats, "provider_calls": 0,
             "provider_cost_usd": 0,
             "actor_unchanged": before == after,
             "stable_baseline": stable_baseline,
             "stable_candidate": stable_candidate,
             "baseline": baseline, "candidate": candidate}
    OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()
    value = run(args.repeats)
    print(f"P01 stability: baseline={value['stable_baseline']} "
          f"candidate={value['stable_candidate']} "
          f"actor_unchanged={value['actor_unchanged']} "
          f"repeats={value['repeats']}")
    return 0 if (value["stable_baseline"] and value["stable_candidate"]
                 and value["actor_unchanged"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
