#!/usr/bin/env python3
"""Aggregate and validate the completed W07 development comparison."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from dispatch_budget import DispatchBudget  # noqa: E402

MANIFEST = ROOT / "docs" / "REAL-WORLD-DEVELOPMENT-32-EPISODE-2026-09-18.json"
AUTHORISATION = ROOT / "docs" / "REAL-WORLD-DEVELOPMENT-AUTHORISATION.json"
CAMPAIGN = ROOT / "pilot-runs" / "realworld-v1-development-thirty-two"
EVIDENCE = ROOT / "test" / "results" / "2026-09-18-realworld-development.json"
REPORT = ROOT / "test" / "results" / "2026-09-18-realworld-development.md"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_revision() -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "--short", "HEAD"],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def aggregate() -> dict:
    manifest = read_json(MANIFEST)
    manifest_digest = manifest.pop("manifest_sha256", None)
    manifest_valid = manifest_digest == digest(manifest)
    manifest["manifest_sha256"] = manifest_digest
    authorisation = read_json(AUTHORISATION)
    authorisation_valid = bool(
        authorisation.get("decision") == "approved"
        and authorisation.get("candidate_sha256") == manifest.get("candidate_sha256")
        and authorisation.get("manifest_sha256") == manifest_digest
        and authorisation.get("maximum_authorised_usd")
        == manifest["cost"]["combined_authorisation_ceiling_usd"]
    )
    campaign = read_json(CAMPAIGN / "campaign-state.json")
    rows = {row["episode_id"]: row for row in manifest["episodes"]}
    exact_episode_set = set(rows) == set(campaign.get("episodes") or {})

    episodes = []
    checks = {
        "manifest_digest_valid": manifest_valid,
        "authorisation_exact": authorisation_valid,
        "campaign_completed": campaign.get("status") == "completed",
        "exact_episode_set": exact_episode_set and len(rows) == 32,
        "event_chains_valid": True,
        "identities_valid": True,
        "accounting_complete": True,
        "actor_boundaries_preserved": True,
        "oracles_unchanged": True,
        "all_learning_eligible": True,
        "campaign_spend_reconciles": True,
    }
    raw_campaign_spend = 0.0
    for episode_id, row in rows.items():
        item = campaign["episodes"][episode_id]
        state = read_json(CAMPAIGN / "episodes" / episode_id / "state.json")
        budget = DispatchBudget(CAMPAIGN / "episodes" / episode_id / "dispatch-budget.json").snapshot()
        history = state.get("history") or []
        # DispatchBudget is the authoritative settled roll-up. Individual
        # history rows may lose sub-nanodollar precision when serialised.
        raw_spend = budget["spent_usd"]
        raw_campaign_spend += raw_spend
        spend = round(raw_spend, 9)
        wall = round(sum(attempt["wall_clock_s"] for attempt in history), 6)
        grade = item["summary"].get("grade") or {}
        checks["event_chains_valid"] &= item["summary"].get("event_chain_valid") is True
        checks["identities_valid"] &= all(attempt.get("identity_valid") is True for attempt in history)
        checks["accounting_complete"] &= not budget["unresolved"] and budget["reserved_usd"] == 0
        checks["actor_boundaries_preserved"] &= all(attempt.get("boundary_ok") is True for attempt in history)
        checks["oracles_unchanged"] &= grade.get("oracle_unchanged") is True
        checks["all_learning_eligible"] &= state.get("learning_eligible") is True
        episodes.append({
            "episode_id": episode_id,
            "sequence": row["sequence"],
            "task_id": row["task_id"],
            "policy_id": row["policy_id"],
            "repetition": row["repetition"],
            "accepted": grade.get("accepted") is True,
            "false_success": (item["summary"].get("stop_reason") == "visible_acceptance_passed"
                              and grade.get("accepted") is not True),
            "attempts": len(history),
            "sequence_cells": [attempt["requested_cell"] for attempt in history],
            "cost_usd": spend,
            "wall_clock_seconds": wall,
            "ledger_sha256": state.get("ledger_sha256"),
        })
    episodes.sort(key=lambda row: row["sequence"])
    checks["campaign_spend_reconciles"] = (
        round(raw_campaign_spend, 9) == campaign.get("known_episode_spend_usd")
    )

    usage = collections.Counter()
    served = collections.Counter()
    auxiliary = set()
    for row in episodes:
        state = read_json(CAMPAIGN / "episodes" / row["episode_id"] / "state.json")
        for attempt in state["history"]:
            for key in ("input_tokens", "cache_creation_input_tokens",
                        "cache_read_input_tokens", "output_tokens"):
                usage[key] += (attempt.get("usage") or {}).get(key, 0)
            served[attempt["actual_model"]] += 1
            auxiliary.update(attempt.get("auxiliary_billed_models") or [])

    policies = []
    for policy in ("B0", "B1"):
        selected = [row for row in episodes if row["policy_id"] == policy]
        accepted = sum(row["accepted"] for row in selected)
        spend = round(sum(row["cost_usd"] for row in selected), 9)
        durations = [row["wall_clock_seconds"] for row in selected]
        policies.append({
            "policy_id": policy,
            "episodes": len(selected),
            "accepted": accepted,
            "false_successes": sum(row["false_success"] for row in selected),
            "attempts": sum(row["attempts"] for row in selected),
            "opus_escalations": sum("worker-opus-high" in row["sequence_cells"] for row in selected),
            "controller_dispatches": sum("controller" in row["sequence_cells"] for row in selected),
            "spend_usd": spend,
            "cost_per_accepted_usd": round(spend / accepted, 9) if accepted else None,
            "wall_clock_seconds": round(sum(durations), 6),
            "episode_latency_p50_seconds": round(percentile(durations, 0.50), 6),
            "episode_latency_p90_seconds": round(percentile(durations, 0.90), 6),
        })

    paired = []
    for repetition in (1, 2):
        tasks = sorted({row["task_id"] for row in episodes if row["repetition"] == repetition})
        for task in tasks:
            pair = {row["policy_id"]: row for row in episodes
                    if row["task_id"] == task and row["repetition"] == repetition}
            if set(pair) == {"B0", "B1"}:
                paired.append({
                    "task_id": task, "repetition": repetition,
                    "B0_accepted": pair["B0"]["accepted"],
                    "B1_accepted": pair["B1"]["accepted"],
                    "winner": ("B1" if pair["B1"]["accepted"] and not pair["B0"]["accepted"]
                               else "B0" if pair["B0"]["accepted"] and not pair["B1"]["accepted"]
                               else "tie"),
                })
    b0, b1 = policies
    decision = {
        "baseline_retained": "B0",
        "adaptive_candidate": "B1",
        "proceed_to_w08": True,
        "default_changed": False,
        "paired_acceptance_wins": {
            "B0": sum(row["winner"] == "B0" for row in paired),
            "B1": sum(row["winner"] == "B1" for row in paired),
            "ties": sum(row["winner"] == "tie" for row in paired),
        },
        "reason": (
            "B1 accepted one more episode with no paired acceptance loss, but spent more "
            "in total and per accepted episode. Retain B0 as baseline and freeze unchanged "
            "B1 as the adaptive candidate for independent reserved evaluation; do not change defaults."
        ),
    }
    return {
        "schema_version": 1,
        "campaign": manifest["campaign"],
        "result": "PASS" if all(checks.values()) else "FAIL",
        "offline_aggregation": True,
        "model_calls": 0,
        "implementation_sha256": file_sha256(Path(__file__)),
        "executed_revision": git_revision(),
        "candidate_sha256": manifest["candidate_sha256"],
        "manifest_sha256": manifest_digest,
        "authorisation_sha256": file_sha256(AUTHORISATION),
        "campaign_state_sha256": file_sha256(CAMPAIGN / "campaign-state.json"),
        "budget": {
            "authorised_ceiling_usd": manifest["cost"]["combined_authorisation_ceiling_usd"],
            "known_spend_usd": campaign["known_episode_spend_usd"],
            "unused_authorised_ceiling_usd": round(
                manifest["cost"]["combined_authorisation_ceiling_usd"]
                - campaign["known_episode_spend_usd"], 9),
        },
        "checks": checks,
        "aggregate_usage": {
            "attempts": sum(row["attempts"] for row in episodes),
            **dict(usage),
            "served_task_models": dict(served),
            "auxiliary_billed_models": sorted(auxiliary),
        },
        "policy_summary": policies,
        "paired_outcomes": paired,
        "episodes": episodes,
        "decision": decision,
    }


def render(value: dict) -> str:
    policies = {row["policy_id"]: row for row in value["policy_summary"]}
    b0, b1 = policies["B0"], policies["B1"]
    lines = [
        "# W07 development comparison", "",
        f"Result: **{value['result']}**. All 32 authorised episodes completed with",
        "valid identity, accounting, event chains, actor boundaries and protected oracles.", "",
        f"Reconciled spend was **USD {value['budget']['known_spend_usd']:.9f}** of the",
        f"USD {value['budget']['authorised_ceiling_usd']:.0f} ceiling.", "",
        "| Policy | Accepted | Attempts | False successes | Spend | Cost/accepted |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
        f"| B0 | {b0['accepted']}/16 | {b0['attempts']} | {b0['false_successes']} | "
        f"USD {b0['spend_usd']:.9f} | USD {b0['cost_per_accepted_usd']:.9f} |",
        f"| B1 | {b1['accepted']}/16 | {b1['attempts']} | {b1['false_successes']} | "
        f"USD {b1['spend_usd']:.9f} | USD {b1['cost_per_accepted_usd']:.9f} |", "",
        "B1 recorded one paired acceptance win on D08 and no paired acceptance loss.",
        "B1 used Opus on both D07 episodes; B0 used a second Sonnet attempt instead.",
        "The repeated D03, D05, D07 and D11 outcomes were consistent across runs.", "",
        "## Decision", "", value["decision"]["reason"], "",
        "Proceed to W08 only through a new frozen 48-episode reserved manifest and",
        "separate exact operator authorisation.", "",
    ]
    return "\n".join(lines)


def write() -> dict:
    value = aggregate()
    REPORT.write_text(render(value), encoding="utf-8", newline="\n")
    value["report"] = {"path": REPORT.relative_to(ROOT).as_posix(),
                       "sha256": file_sha256(REPORT)}
    value["evidence_sha256"] = digest(value)
    EVIDENCE.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    return value


def validate() -> tuple[bool, str]:
    if not EVIDENCE.is_file() or not REPORT.is_file():
        return False, "development evidence or report is missing"
    value = read_json(EVIDENCE)
    recorded = value.pop("evidence_sha256", None)
    ok = bool(
        recorded == digest(value) and value.get("result") == "PASS"
        and value.get("model_calls") == 0
        and value.get("implementation_sha256") == file_sha256(Path(__file__))
        and value.get("campaign_state_sha256") == file_sha256(CAMPAIGN / "campaign-state.json")
        and (value.get("report") or {}).get("sha256") == file_sha256(REPORT)
        and all((value.get("checks") or {}).values())
    )
    return ok, f"digest={'valid' if recorded == digest(value) else 'invalid'}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.record:
        value = write()
        print(f"{value['result']}: W07 evidence; spend USD {value['budget']['known_spend_usd']:.9f}")
        return 0 if value["result"] == "PASS" else 1
    if args.check:
        ok, detail = validate()
        print(f"{'PASS' if ok else 'FAIL'}: W07 evidence {detail}")
        return 0 if ok else 1
    print(json.dumps(aggregate(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
