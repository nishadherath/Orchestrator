#!/usr/bin/env python3
"""Analyse the stopped v6 pairs and the prospective v7 continuation distinctly."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import controller_x5_v6_pilot as old
import controller_x5_v7_pilot as pilot
import controller_x5_v7_pilot_grade as grader
import dispatch_budget


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def p95(values: list[float]) -> float | None:
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1] if ordered else None


def family(task: str) -> str:
    return ("proposed-suitable" if task in pilot.screen.CASE_DIRS else
            "ordinary-worker" if task == "N01-D1" else "missing-decision")


def group(rows: list[dict]) -> dict:
    functional = [row["grade"]["functional_score"] for row in rows
                  if row["grade"]["functional_score"] is not None]
    return {"episodes": len(rows),
            "historical_posthoc": sum(row["provenance"] == "historical-posthoc"
                                      for row in rows),
            "accepted": sum(bool(row["grade"]["accepted"]) for row in rows),
            "functional_accepted": sum(row["grade"]["functional_accepted"] is True
                                       for row in rows),
            "mean_functional_score": mean(functional),
            "mean_quality": mean([row["grade"]["quality"] for row in rows]),
            "mean_components": {name: mean([row["grade"]["components"][name]
                                            for row in rows])
                                for name in ("M", "E", "D", "N", "H")},
            "critical_errors": sum(row["grade"]["critical_violation"] for row in rows),
            "false_successes": sum(row["grade"]["false_success"] for row in rows),
            "total_cost_usd": round(sum(row["budget_spent_usd"] for row in rows), 9),
            "mean_cost_usd": mean([row["budget_spent_usd"] for row in rows]),
            "mean_elapsed_s": mean([row["elapsed_s"] for row in rows]),
            "p95_elapsed_s": p95([row["elapsed_s"] for row in rows]),
            "worker_attempts": sum(row["worker_attempt_count"] for row in rows),
            "controller_invocations": sum(row["controller_invocations"] for row in rows),
            "controller_role_calls": sum(row["controller_role_call_count"] or 0
                                         for row in rows)}


def role_evidence(row: dict) -> list[dict]:
    if not row["controller_invocations"]:
        return []
    actor = Path(row["project"])
    role_dir = Path(row["controller_run_dir"] or "")
    if not role_dir.is_relative_to(actor):
        raise pilot.PilotError("Controller role path escaped its actor")
    budget = dispatch_budget.DispatchBudget(
        role_dir / "dispatch-budget.json").snapshot()
    if (budget["unresolved"] or len(budget["invocations"]) != row["controller_role_call_count"]
            or abs(budget["spent_usd"] - row["controller_role_cost_usd"]) > 1e-9):
        raise pilot.PilotError("Controller role budget differs from episode receipt")
    return [{"role": call["metadata"].get("role"),
             "phase": call["metadata"].get("phase"),
             "requested_cell": call["metadata"].get("cell"),
             "status": (call.get("telemetry") or {}).get("status"),
             "actual_model": ((call.get("telemetry") or {}).get("identity") or {}).get("actual_model"),
             "identity_valid": ((call.get("telemetry") or {}).get("identity") or {}).get("identity_valid"),
             "cost_usd": call.get("cost_usd")}
            for call in budget["invocations"].values()]


def analyse(manifest: dict) -> dict:
    pilot.validate(manifest)
    historical_manifest = old.load(pilot.V6_MANIFEST)
    rows = []
    for spec in historical_manifest["episodes"][:6]:
        row = old.load(old.RUN_DIR / f"{spec['sequence']:03d}-result.json")
        actor = old.project(historical_manifest, spec)
        grade = grader.grade(spec["task_id"], actor, historical_manifest)
        rows.append({**row, "grade": grade, "provenance": "historical-posthoc"})
    for spec in manifest["episodes"]:
        row = pilot.load(pilot.RUN_DIR / f"{spec['sequence']:03d}-result.json")
        state = pilot.executor(manifest, spec).status(pilot.root_id(manifest, spec))
        if (row.get("status") != "completed" or row.get("manifest_sha256") != manifest["manifest_sha256"]
                or row.get("task_id") != spec["task_id"] or row.get("arm") != spec["arm"]
                or row.get("sequence") != spec["sequence"]
                or row.get("required_admission_met") is not True
                or row.get("budget_unresolved") or state["budget"]["unresolved"]
                or row.get("budget_spent_usd") != state["budget"]["spent_usd"]
                or row.get("budget_spent_usd", 1e9) > spec["maximum_usd"]
                or row.get("grade") is None):
            raise pilot.PilotError(f"v7 episode is incomplete: {spec['sequence']}")
        fresh_grade = grader.grade(spec["task_id"], pilot.project(manifest, spec), manifest)
        if fresh_grade != row["grade"]:
            raise pilot.PilotError(f"v7 actor or protected score changed: {spec['sequence']}")
        rows.append({**row, "provenance": "prospective-v7"})
    if len(rows) != 18 or sum(row["provenance"] == "prospective-v7" for row in rows) != 12:
        raise pilot.PilotError("combined development comparison lacks 18 episodes")
    v7_cost = round(sum(row["budget_spent_usd"] for row in rows[6:]), 9)
    if v7_cost > manifest["maximum_authorised_usd"]:
        raise pilot.PilotError("v7 continuation exceeded its frozen ceiling")
    by_task = {task: {row["arm"]: row for row in rows if row["task_id"] == task}
               for task in pilot.screen.TASKS}
    pairs = []
    for task, arms in by_task.items():
        if set(arms) != {"B", "S", "A"}:
            raise pilot.PilotError(f"task lacks matched arms: {task}")
        deltas = {}
        for label, left, right in (("A_minus_S", "A", "S"), ("S_minus_B", "S", "B")):
            a, b = arms[left], arms[right]
            deltas[label] = {"quality": round(a["grade"]["quality"] - b["grade"]["quality"], 6),
                             "cost_usd": round(a["budget_spent_usd"] - b["budget_spent_usd"], 9),
                             "elapsed_s": round(a["elapsed_s"] - b["elapsed_s"], 3),
                             "accepted": int(a["grade"]["accepted"]) - int(b["grade"]["accepted"])}
        pairs.append({"task_id": task, "family": family(task),
                      "provenance": arms["A"]["provenance"], **deltas})
    roles = [role for row in rows for role in role_evidence(row)]
    attempts = [attempt for row in rows for attempt in row["worker_attempts"]]
    suitable_a = [row for row in rows if row["arm"] == "A"
                  and family(row["task_id"]) == "proposed-suitable"]
    return {"schema_version": 1, "stage": "controller-x5-v7-development-continuation",
            "manifest_sha256": manifest["manifest_sha256"], "episodes": 18,
            "historical_posthoc_episodes": 6, "prospective_v7_episodes": 12,
            "historical_v6_cost_usd": round(sum(row["budget_spent_usd"] for row in rows[:6]), 9),
            "v7_cost_usd": v7_cost,
            "combined_cost_usd": round(sum(row["budget_spent_usd"] for row in rows), 9),
            "by_arm": {arm: group([row for row in rows if row["arm"] == arm])
                       for arm in ("B", "S", "A")},
            "by_family_and_arm": {name: {arm: group([
                row for row in rows if family(row["task_id"]) == name and row["arm"] == arm])
                for arm in ("B", "S", "A")}
                for name in ("proposed-suitable", "ordinary-worker", "missing-decision")},
            "paired_deltas": pairs,
            "automatic_suitable_controller_admissions": sum(
                row["effective_action"] == "controller"
                and row["controller_stage"] == "worker-ready" for row in suitable_a),
            "host_verified_controller_worker_results": sum(
                row["grade"]["functional_accepted"] is True
                and row["controller_stage"] == "worker-ready"
                and row["worker_attempt_count"] > 0 for row in suitable_a),
            "frontier_roles": [role for role in roles if role["actual_model"] == "claude-fable-5-1"
                               and role["identity_valid"] is True],
            "controller_roles": roles,
            "clarification_action": by_task["C08-D2"]["A"]["effective_action"],
            "ordinary_action": by_task["N01-D1"]["A"]["effective_action"],
            "worker_models": sorted({attempt["actual_model"] for attempt in attempts
                                     if attempt["actual_model"]}),
            "worker_identity_failures": sum(attempt["identity_valid"] is False
                                            for attempt in attempts),
            "worker_served_effort_unknown": sum(attempt["served_effort"] is None
                                                for attempt in attempts),
            "interpretation": "Hybrid development evidence; six pairs were rescored post hoc and X6 remains unseen. No default promotion authority."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyse(pilot.load(args.manifest))
    if args.out.exists() or args.out.is_symlink():
        raise pilot.PilotError("analysis output path already exists")
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"episodes": result["episodes"],
                      "combined_cost_usd": result["combined_cost_usd"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
