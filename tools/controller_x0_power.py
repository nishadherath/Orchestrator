#!/usr/bin/env python3
"""Prospective, provider-free feasibility analysis for the capped X6 design.

All distributions are assumptions. Repetitions never increase the independent
task count. The bootstrap screen is exploratory; it has no promotion authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

from worker_qualification_power import exact_power, zero_event_upper


def percentile(values: list[float], probability: float) -> float:
    """Linear empirical quantile, with explicit boundary checks."""
    if (not values or not 0 <= probability <= 1
            or any(not math.isfinite(x) for x in values)):
        raise ValueError("quantile needs finite observations and probability in [0,1]")
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    low = math.floor(index)
    high = math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def paired_quality_interval(families: list[list[float]], rng: random.Random,
                            resamples: int = 1000) -> tuple[float, float]:
    """Two-stage paired bootstrap: families, then task deltas within family.

Each input is already the mean of the A-minus-S repetitions for one task.
Both arms stay paired. Equal tasks per family are required by this contract.
"""
    if (not families or not families[0] or type(resamples) is not int or resamples < 2
            or any(len(row) != len(families[0]) for row in families)
            or any(not math.isfinite(x) or not -100 <= x <= 100
                   for row in families for x in row)):
        raise ValueError("balanced non-empty finite task deltas in [-100,100] are required")
    means = []
    count, width = len(families), len(families[0])
    for _ in range(resamples):
        total = 0.0
        for _ in range(count):
            family = families[rng.randrange(count)]
            total += sum(family[rng.randrange(width)] for _ in range(width))
        means.append(total / (count * width))
    return percentile(means, .025), percentile(means, .975)


def simulate_quality(*, tasks: int, loss: float, win: float, magnitude: float,
                     simulations: int, resamples: int, seed: int,
                     family_shared: bool) -> dict:
    """Estimate the isolated +5 quality gate under a stated categorical model."""
    if (type(tasks) is not int or tasks < 2 or tasks % 2
            or type(simulations) is not int or simulations < 2
            or not all(math.isfinite(v) for v in (loss, win, magnitude))
            or min(loss, win) < 0 or loss + win > 1 or not 0 < magnitude <= 100):
        raise ValueError("use even tasks, at least two simulations and valid probabilities/magnitude")
    rng = random.Random(seed)
    passes, covered = 0, 0
    lower_bounds = []
    mean = (win - loss) * magnitude
    def draw() -> float:
        value = rng.random()
        return -magnitude if value < loss else magnitude if value < loss + win else 0.0

    for _ in range(simulations):
        families = []
        for _ in range(tasks // 2):
            first = draw()
            families.append([first, first if family_shared else draw()])
        low, high = paired_quality_interval(families, rng, resamples)
        passes += low > 5.0
        covered += low <= mean <= high
        lower_bounds.append(low)
    rate = passes / simulations
    return {"tasks": tasks, "families": tasks // 2, "repetitions_per_arm": 2,
            "assumed_loss_probability": loss, "assumed_win_probability": win,
            "assumed_delta_magnitude": magnitude, "assumed_mean_delta": mean,
            "family_shared_outcomes": family_shared, "simulations": simulations,
            "bootstrap_resamples": resamples, "seed": seed,
            "quality_gate_pass_fraction": rate,
            "monte_carlo_standard_error": math.sqrt(rate * (1 - rate) / simulations),
            "empirical_interval_coverage": covered / simulations,
            "median_lower_bound": statistics.median(lower_bounds)}


def analyse(simulations: int = 600, resamples: int = 400) -> dict:
    scenarios = (("null", .15, .15), ("modest", .10, .40), ("large", .05, .70))
    quality = []
    for index, (name, loss, win) in enumerate(scenarios):
        for shared in (False, True):
            row = simulate_quality(tasks=16, loss=loss, win=win, magnitude=20,
                                   simulations=simulations, resamples=resamples,
                                   seed=27092026 + index * 2 + int(shared), family_shared=shared)
            quality.append({"scenario": name, **row})
    return {
        "schema_version": 1, "stage": "X0", "provider_calls": 0,
        "source_sha256": {name: hashlib.sha256(
            (Path(__file__).resolve().parent / name).read_bytes()).hexdigest()
            for name in ("controller_x0_power.py", "worker_qualification_power.py")},
        "decision": "24-task-X6-exploratory-only-no-promotion-authority",
        "zero_candidate_only_harm_upper_95": {str(n): zero_event_upper(n) for n in (8, 16, 24, 48, 59)},
        "minimum_zero_event_tasks_for_upper_below_5_percent":
            math.floor(math.log(.05) / math.log(.95)) + 1,
        "sign_test_sensitivity": [
            {"tasks": n, "assumed_win_probability": win, "assumed_loss_probability": loss,
             "one_sided_alpha": .025, "directional_power": exact_power(n, win, loss, .025)}
            for n in (16, 24, 48) for win, loss in ((.20, .05), (.35, .05), (.50, .05))],
        "quality_gate_simulations": quality,
        "limits": [
            "Assumed task distributions, not empirical Controller outcomes.",
            "The sign test examines direction, not a +5 quality margin or acceptance non-inferiority.",
            "Quality simulations examine one gate; all-gate power cannot be greater.",
            "Eight suitable families and two tasks each yield fragile bootstrap coverage.",
            "Zero-harm bounds assume independent tasks; shared family failures reduce effective information.",
            "Two repetitions per arm give 96 episodes, not 96 independent tasks.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyse()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
