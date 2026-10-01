#!/usr/bin/env python3
"""Reconcile the sealed N5 development campaign and report paired outcomes.

This reads only completed D-series run evidence. It cannot launch a worker
and does not inspect or score R-series reserved outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import dispatch_budget
import model_registry
import route
import worker_n5_development as plan
from worker_adapter import digest


class AnalysisError(RuntimeError):
    """The result is incomplete or fails campaign-to-receipt reconciliation."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(rows: list[dict]) -> dict:
    cost = sum(row["spent_usd"] for row in rows)
    return {"episodes": len(rows),
            "accepted": sum(row["grade"]["acceptance"] for row in rows),
            "mean_quality": round(sum(row["grade"]["quality"] for row in rows) / len(rows), 4),
            "critical_errors": sum(row["grade"]["critical_error"] for row in rows),
            "false_successes": sum(row["grade"]["false_success"] for row in rows),
            "cost_usd": round(cost, 9),
            "attempts": sum(row["attempts"] for row in rows)}


def analyse(manifest_path: Path, run: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plan.validate_manifest(manifest, check_host=False)
    campaign_path, budget_path = run / "campaign.json", run / "budget.json"
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    body = {key: value for key, value in campaign.items() if key != "state_sha256"}
    rows = campaign.get("rows")
    if (campaign.get("state_sha256") != digest(body)
            or campaign.get("manifest_sha256") != manifest["manifest_sha256"]
            or campaign.get("status") != "complete"
            or campaign.get("inflight") is not None
            or campaign.get("next_sequence") != 37
            or not isinstance(rows, list) or len(rows) != 36):
        raise AnalysisError("development checkpoint is incomplete or altered")
    budget = dispatch_budget.DispatchBudget(
        budget_path, manifest["cost"]["maximum_usd"], scope="task_dispatch").snapshot()
    if (budget["unresolved"] or budget["breached"] or len(budget["invocations"]) != 36):
        raise AnalysisError("development campaign budget is unresolved")
    usage: dict[str, int] = defaultdict(int)
    models: dict[str, int] = defaultdict(int)
    efforts: dict[str, int] = defaultdict(int)
    call_time = 0.0
    paired: dict[str, dict[str, dict]] = defaultdict(dict)
    tasks = {task["id"]: task for task in
             plan.worker_evaluation.load_catalogue(plan.CORPUS)["tasks"]}
    for index, (row, planned) in enumerate(zip(rows, manifest["rows"]), 1):
        if (row.get("sequence") != index or row.get("task_id") != planned["task_id"]
                or row.get("arm") != planned["arm"]
                or row.get("root_state") not in {"accepted", "failed", "partial"}
                or row.get("requested_cells", [None])[0] != planned["selected_cell"]):
            raise AnalysisError(f"row {index} differs from the frozen schedule")
        invocation = digest({"manifest": manifest["manifest_sha256"],
                             "sequence": index})[:32]
        charge = budget["invocations"].get(invocation)
        if (charge is None or charge["state"] != "settled"
                or not math.isclose(charge["cost_usd"], row["spent_usd"],
                                    abs_tol=1e-8)):
            raise AnalysisError(f"row {index} and campaign charge differ")
        root_id = "episode_" + digest({"episode": invocation})[:20]
        actor = run / "actors" / f"row-{index:03d}"
        root_path = actor / ".claude" / "task-executor-v2" / root_id / "root.json"
        record = json.loads(root_path.read_text(encoding="utf-8"))
        checksum = record.pop("record_digest")
        if (checksum != digest(record) or row["root_record_digest"] != digest(record)
                or record["root_id"] != root_id
                or record["state"] != row["root_state"]
                or record["ladder"] != planned["ladder"]
                or len(record["attempts"]) != row["attempts"]):
            raise AnalysisError(f"root {index} differs from its recorded row")
        task = tasks[row["task_id"]]
        oracle_sha = manifest["corpus_files"][task["oracle"]]
        grade = row["grade"]
        if (grade["oracle_sha256"] != oracle_sha
                or grade["actor_app_sha256"] != row["actor_app_sha256"]
                or _sha(actor / "app.py") != row["actor_app_sha256"]
                or grade["false_success"] !=
                (row["root_state"] == "accepted" and not grade["acceptance"])):
            raise AnalysisError(f"grade {index} is not bound to its actor and oracle")
        if list(actor.rglob("*oracle*")):
            raise AnalysisError(f"oracle leaked into actor {index}")
        receipt_cost = 0.0
        for attempt in record["attempts"]:
            receipt = attempt.get("receipt") or {}
            cell = attempt["requested_cell"]
            if (not receipt.get("terminal") or not receipt.get("writer_stopped")
                    or not model_registry.identity_matches(cell,
                                                           receipt.get("actual_model"),
                                                           receipt.get("child_models"))
                    or receipt.get("effort_evidence") !=
                    f"cli-argument:{model_registry.resolve_cell(cell)['effort']}"
                    or type(receipt.get("cost_usd")) not in (int, float)):
                raise AnalysisError(f"attempt identity or receipt invalid in row {index}")
            receipt_cost += receipt["cost_usd"]
            models[receipt["actual_model"]] += 1
            efforts[receipt["effort_evidence"]] += 1
            call_time += receipt.get("wall_clock_s") or 0
            for key in ("input_tokens", "cache_creation_input_tokens",
                        "cache_read_input_tokens", "output_tokens"):
                value = (receipt.get("usage") or {}).get(key)
                if type(value) is int:
                    usage[key] += value
        if not math.isclose(receipt_cost, row["spent_usd"], abs_tol=1e-8):
            raise AnalysisError(f"attempt receipts and root charge differ in row {index}")
        paired[row["task_id"]][row["arm"]] = row
    if any(set(arms) != set(plan.ARMS) for arms in paired.values()):
        raise AnalysisError("a task is missing a paired arm")
    by_arm = {arm: _summary([row for row in rows if row["arm"] == arm])
              for arm in plan.ARMS}
    by_complexity = {level: {arm: _summary([
        row for row in rows if row["arm"] == arm and
        manifest["assessments"][row["task_id"]]["facts"]["complexity"] == level])
        for arm in plan.ARMS} for level in ("routine", "moderate", "complex")}
    pairs = [{"task_id": ident,
              "complexity": manifest["assessments"][ident]["facts"]["complexity"],
              "candidate_minus_b0_quality": round(
                  arms["candidate"]["grade"]["quality"] - arms["B0"]["grade"]["quality"], 4),
              "candidate_minus_b0_cost_usd": round(
                  arms["candidate"]["spent_usd"] - arms["B0"]["spent_usd"], 9),
              "alternative_minus_b0_quality": round(
                  arms["alternative"]["grade"]["quality"] - arms["B0"]["grade"]["quality"], 4),
              "alternative_minus_b0_cost_usd": round(
                  arms["alternative"]["spent_usd"] - arms["B0"]["spent_usd"], 9)}
             for ident, arms in sorted(paired.items())]
    result = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
              "campaign_sha256": _sha(campaign_path), "budget_sha256": _sha(budget_path),
              "status": "reconciled", "episodes": len(rows),
              "provider_calls": sum(row["attempts"] for row in rows),
              "reported_api_equivalent_cost_usd": round(sum(
                  row["spent_usd"] for row in rows), 9),
              "call_wall_time_s": round(call_time, 3),
              "model_calls": dict(sorted(models.items())),
              "requested_effort_evidence": dict(sorted(efforts.items())),
              "usage": dict(sorted(usage.items())), "by_arm": by_arm,
              "by_complexity": by_complexity, "pairs": pairs,
              "limits": ["one run per task-arm", "synthetic single-file tasks",
                         "served effort not independently reported",
                         "development data; reserved tasks not graded"]}
    return {**result, "analysis_sha256": digest(result)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = analyse(args.manifest, args.run)
    except (OSError, ValueError, KeyError, AnalysisError) as exc:
        print(f"N5 analysis blocked: {exc}", file=sys.stderr)
        return 2
    route._atomic_write_bytes(args.output, (json.dumps(result, indent=2,
                                                       sort_keys=True) + "\n").encode())
    print(f"N5 reconciled: {result['episodes']} episodes, {result['provider_calls']} "
          f"calls, USD {result['reported_api_equivalent_cost_usd']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
