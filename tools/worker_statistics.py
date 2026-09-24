#!/usr/bin/env python3
"""Predeclared worker N6 paired bounds and provider-free power preflight.

The independent unit is a task mechanism. Callers aggregate two scheduled
repetitions in each arm before passing one row per task here. This module is
deliberately independent of task outcomes and provider APIs.
"""
from __future__ import annotations

import json
import math
import random

TAIL = 0.0125  # two CP tails share alpha_A=.025; alpha_Q=.025


def _upper_tail(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, j) * p**j * (1 - p)**(n-j)
               for j in range(k, n + 1))


def _lower_tail(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, j) * p**j * (1 - p)**(n-j)
               for j in range(k + 1))


def cp_lower(k: int, n: int, tail: float = TAIL) -> float:
    if not 0 <= k <= n or n < 1:
        raise ValueError("invalid binomial count")
    if k == 0:
        return 0.0
    low, high = 0.0, 1.0
    for _ in range(65):
        mid = (low + high) / 2
        if _upper_tail(k, n, mid) < tail:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def cp_upper(k: int, n: int, tail: float = TAIL) -> float:
    if not 0 <= k <= n or n < 1:
        raise ValueError("invalid binomial count")
    if k == n:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(65):
        mid = (low + high) / 2
        if _lower_tail(k, n, mid) > tail:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def bounds(rows: list[dict]) -> dict:
    """Rows contain task-level B0/candidate acceptance and 0..100 quality."""
    n = len(rows)
    if n == 0:
        raise ValueError("at least one independent task is required")
    wins = losses = 0
    differences = []
    for row in rows:
        if (set(row) != {"b0_accept", "candidate_accept", "b0_quality",
                         "candidate_quality"}
                or type(row["b0_accept"]) is not bool
                or type(row["candidate_accept"]) is not bool):
            raise ValueError("invalid paired task row")
        bq, cq = row["b0_quality"], row["candidate_quality"]
        if (type(bq) not in (int, float) or type(cq) not in (int, float)
                or not math.isfinite(bq) or not math.isfinite(cq)
                or not 0 <= bq <= 100 or not 0 <= cq <= 100):
            raise ValueError("quality must be finite and bounded 0..100")
        wins += row["candidate_accept"] and not row["b0_accept"]
        losses += row["b0_accept"] and not row["candidate_accept"]
        differences.append(cq - bq)
    mean = sum(differences) / n
    return {"tasks": n, "wins": wins, "losses": losses,
            "acceptance_delta": (wins - losses) / n,
            "acceptance_lower": cp_lower(wins, n) - cp_upper(losses, n),
            "quality_delta": mean,
            "quality_lower": max(-100.0, mean - 200 * math.sqrt(math.log(1 / .025) / (2 * n)))}


def simulate(*, tasks: int = 12, trials: int = 1000, seed: int = 20260924) -> dict:
    """Illustrative task-level power under explicit, reproducible assumptions."""
    if tasks < 1 or trials < 1:
        raise ValueError("positive tasks and trials required")
    rng = random.Random(seed)
    scenarios = [
        ("equal", .0, .0, 0),
        ("modest_gain", .20, .05, 10),
        ("large_gain", .50, .02, 35),
        ("extreme_gain", .90, .0, 80),
    ]
    output = {}
    quality_penalty = 200 * math.sqrt(math.log(1 / .025) / (2 * tasks))
    # Acceptance draws are mutually exclusive. Quality is a fixed task-level
    # mean in this illustrative calculation; variance would lower power.
    for name, win_rate, loss_rate, mean_quality_gain in scenarios:
        eligible = 0
        for _ in range(trials):
            wins = losses = 0
            for _ in range(tasks):
                draw = rng.random()
                wins += draw < win_rate
                losses += win_rate <= draw < win_rate + loss_rate
            la = cp_lower(wins, tasks) - cp_upper(losses, tasks)
            lq = max(-100.0, mean_quality_gain - quality_penalty)
            eligible += la > -.05 and lq > -5
        output[name] = {"candidate_only_rate": win_rate,
                        "b0_only_rate": loss_rate,
                        "assumed_quality_gain": mean_quality_gain,
                        "quality_lower": round(lq, 3),
                        "fraction_passing_both_quality_floors": round(eligible / trials, 4)}
    return {"tasks": tasks, "trials": trials, "seed": seed,
            "quality_penalty_points": round(quality_penalty, 3),
            "scenarios": output,
            "limits": "Illustrative task-level scenarios, not measured power or population inference."}


if __name__ == "__main__":
    print(json.dumps(simulate(), indent=2, sort_keys=True))
