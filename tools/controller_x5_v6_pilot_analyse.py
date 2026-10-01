#!/usr/bin/env python3
"""Reconcile all X5 v6 pilot attempts and report descriptive paired outcomes."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import controller_x5_v6_pilot as pilot


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def family(task: str) -> str:
    if task in pilot.screen.CASE_DIRS:
        return "proposed-suitable"
    return "ordinary-worker" if task == "N01-D1" else "missing-decision"


def group(rows: list[dict]) -> dict:
    costs = [row["budget_spent_usd"] for row in rows]
    times = [row["elapsed_s"] for row in rows]
    qualities = [row["grade"]["quality"] for row in rows]
    return {"episodes": len(rows), "accepted": sum(row["grade"]["accepted"] for row in rows),
            "critical_errors": sum(row["grade"]["critical_violation"] for row in rows),
            "false_successes": sum(row["grade"]["false_success"] for row in rows),
            "mean_quality": mean(qualities), "total_cost_usd": round(sum(costs), 9),
            "mean_cost_usd": mean(costs), "mean_elapsed_s": mean(times),
            "p95_elapsed_s": p95(times),
            "mean_components": {name: mean([row["grade"]["components"][name]
                                            for row in rows])
                                for name in ("M", "E", "D", "N", "H")},
            "controller_invocations": sum(row["controller_invocations"] for row in rows),
            "controller_role_calls": sum(row["controller_role_call_count"] or 0
                                         for row in rows),
            "worker_attempts": sum(row["worker_attempt_count"] for row in rows)}


def analyse(manifest: dict) -> dict:
    pilot.validate(manifest)
    rows = []
    for spec in manifest["episodes"]:
        row = pilot.load(pilot.RUN_DIR / f"{spec['sequence']:03d}-result.json")
        if (row.get("manifest_sha256") != manifest["manifest_sha256"]
                or row.get("sequence") != spec["sequence"]
                or row.get("task_id") != spec["task_id"]
                or row.get("arm") != spec["arm"]
                or row.get("status") != "completed"
                or row.get("budget_unresolved")
                or row.get("required_admission_met") is not True
                or row.get("grade") is None
                or row.get("budget_spent_usd", 1e9) > spec["maximum_usd"]):
            raise pilot.PilotError(f"pilot episode is incomplete or inconsistent: {spec['sequence']}")
        rows.append(row)
    total = round(sum(row["budget_spent_usd"] for row in rows), 9)
    if total > manifest["maximum_authorised_usd"]:
        raise pilot.PilotError("pilot spent above the frozen ceiling")
    by_task = {task: {row["arm"]: row for row in rows if row["task_id"] == task}
               for task in pilot.screen.TASKS}
    pairs = []
    for task, arms in by_task.items():
        if set(arms) != {"B", "S", "A"}:
            raise pilot.PilotError(f"pilot task lacks matched arms: {task}")
        pairs.append({"task_id": task, "family": family(task),
                      "A_minus_S": {"quality": round(arms["A"]["grade"]["quality"]
                                                   - arms["S"]["grade"]["quality"], 6),
                                    "cost_usd": round(arms["A"]["budget_spent_usd"]
                                                      - arms["S"]["budget_spent_usd"], 9),
                                    "elapsed_s": round(arms["A"]["elapsed_s"]
                                                       - arms["S"]["elapsed_s"], 3),
                                    "accepted": int(arms["A"]["grade"]["accepted"])
                                                - int(arms["S"]["grade"]["accepted"])},
                      "S_minus_B": {"quality": round(arms["S"]["grade"]["quality"]
                                                   - arms["B"]["grade"]["quality"], 6),
                                    "cost_usd": round(arms["S"]["budget_spent_usd"]
                                                      - arms["B"]["budget_spent_usd"], 9)}})
    attempts = [attempt for row in rows for attempt in row["worker_attempts"]]
    return {"schema_version": 1, "stage": "controller-x5-v6-development-pilot",
            "manifest_sha256": manifest["manifest_sha256"],
            "episodes": len(rows), "total_cost_usd": total,
            "by_arm": {arm: group([row for row in rows if row["arm"] == arm])
                       for arm in ("B", "S", "A")},
            "by_family_and_arm": {name: {arm: group([
                row for row in rows if family(row["task_id"]) == name
                and row["arm"] == arm]) for arm in ("B", "S", "A")}
                for name in ("proposed-suitable", "ordinary-worker", "missing-decision")},
            "paired_deltas": pairs,
            "actual_worker_models": sorted({attempt["actual_model"] for attempt in attempts
                                            if attempt["actual_model"]}),
            "worker_identity_failures": sum(attempt["identity_valid"] is False
                                            for attempt in attempts),
            "worker_served_effort_unknown": sum(attempt["served_effort"] is None
                                                for attempt in attempts),
            "automatic_controller_admissions": sum(
                row["controller_invocations"] for row in rows if row["arm"] == "A"),
            "frontier_trial": [row["sequence"] for row in rows
                               if row["controller_profile"] == "frontier-candidate"
                               and row["controller_invocations"] == 1],
            "clarification_action": by_task["C08-D2"]["A"]["effective_action"],
            "interpretation": "Development evidence only; X6 reserved cases remain unseen."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyse(pilot.load(args.manifest))
    if args.out.exists() or args.out.is_symlink():
        raise pilot.PilotError("pilot analysis output path already exists")
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"episodes": result["episodes"],
                      "total_cost_usd": result["total_cost_usd"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
