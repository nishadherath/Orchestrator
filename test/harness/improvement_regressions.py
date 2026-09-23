#!/usr/bin/env python3
"""Desired-behaviour regressions for open 2026-09-17 audit findings.

The assertions state the target contract. ``KNOWN_OPEN`` marks assertions
that are expected to fail until their implementation stage lands; an
unexpected pass fails this runner so the marker cannot silently outlive the
fix. No model, network, or provider call is made.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import claudep  # noqa: E402
import route  # noqa: E402
import system_controller as controller  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402

KNOWN_OPEN: set[str] = set()


def r1_pending_is_unknown() -> None:
    pending = [{
        "ledger_version": 2,
        "execution_status": "pending",
        "first_cell": "worker-sonnet-low",
        "final_outcome": "unknown",
        "cost_usd": None,
        "wall_clock_s": None,
        "attempts": [{
            "requested_cell": "worker-sonnet-low",
            "status": "pending",
            "outcome": "unknown",
            "cost_usd": None,
            "wall_clock_s": None,
        }],
    } for _ in range(5)]
    means = route.ledger_cell_means(pending, 5)
    assert "worker-sonnet-low" not in means, means


def r2_direct_starts_update_their_own_population() -> None:
    bucket = "mechanical/short/contained"
    failed = [{
        "bucket": bucket,
        "first_cell": "worker-opus-high",
        "final_outcome": "fail",
        "escalations": [],
    } for _ in range(20)]
    post = route.posterior(route.load_priors(), failed, bucket)
    direct = post["rungs"]["worker-opus-high"].get("direct", {})
    assert direct.get("ledger_fails") == 20, post["rungs"]["worker-opus-high"]


def r3_each_call_is_bounded_by_remaining_budget() -> None:
    remaining = 0.60
    reply = claudep.ClaudeCallResult("", 0.0, 0.0, {}, {}, "fake")
    with tempfile.TemporaryDirectory(prefix="r3-budget-") as tmp:
        budget = DispatchBudget(Path(tmp) / "dispatch-budget.json", remaining)
        with mock.patch.object(claudep, "call_claude", return_value=reply) as call:
            controller.LiveRoleRunner(Path(tmp), budget.remaining, budget=budget)(
                "frame", "framer", "test", timeout=1
            )
    assert call.call_args.kwargs["max_budget_usd"] <= remaining, call.call_args


def r5_projection_starts_at_selected_cell() -> None:
    bucket = "open/medium/contained"
    sensitivity, horizon, blast = bucket.split("/")
    failed = [{
        "bucket": bucket,
        "first_cell": "worker-sonnet-low",
        "final_outcome": "fail",
        "escalations": [],
    } for _ in range(20)]
    costs = route.load_cost_table()
    planned = route.plan(sensitivity, horizon, blast, ledger=failed, costs=costs)
    selected_cost = costs["cells"][planned["first"]]["cost_per_run_usd"]
    assert planned["projection"]["cost_usd_expected"] >= selected_cost, planned


def main() -> int:
    cases = {
        "R1": r1_pending_is_unknown,
        "R2": r2_direct_starts_update_their_own_population,
        "R3": r3_each_call_is_bounded_by_remaining_budget,
        "R5": r5_projection_starts_at_selected_cell,
    }
    unexpected: list[str] = []
    labels: list[str] = []
    for finding, case in cases.items():
        try:
            case()
            passed, detail = True, ""
        except AssertionError as exc:
            passed, detail = False, str(exc)[:240]
        if finding in KNOWN_OPEN:
            label = "XPASS" if passed else "XFAIL"
            if passed:
                unexpected.append(f"{finding} passed; remove it from KNOWN_OPEN")
        else:
            label = "PASS" if passed else "FAIL"
            if not passed:
                unexpected.append(f"{finding} regressed: {detail}")
        labels.append(f"{finding}={label}")
    print("; ".join(labels))
    if unexpected:
        print("; ".join(unexpected), file=sys.stderr)
        return 1
    print("PASS: improvement regressions (4 closed, 0 explicitly open; no claude -p calls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
