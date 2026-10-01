#!/usr/bin/env python3
"""Exact power preflight for one frozen worker-routing task stratum.

The independent unit is a task mechanism. A win is a predeclared candidate-
only acceptance or material-quality improvement; a loss is the reverse. Ties
are counted in the task sample but omitted from the conditional sign test.
The probabilities supplied to this script are assumptions, not estimates.
"""
from __future__ import annotations

import argparse
import json
import math


def sign_p_value(wins: int, losses: int) -> float:
    """One-sided exact binomial tail under equal win/loss probability."""
    if (type(wins) is not int or type(losses) is not int
            or min(wins, losses) < 0):
        raise ValueError("win and loss counts must be non-negative integers")
    discordant = wins + losses
    return math.ldexp(sum(math.comb(discordant, k)
                          for k in range(wins, discordant + 1)), -discordant)


def exact_power(tasks: int, win_probability: float, loss_probability: float,
                alpha: float = .025) -> float:
    """Enumerate multinomial task outcomes for the exact directional test."""
    if type(tasks) is not int or tasks < 1:
        raise ValueError("tasks must be a positive integer")
    if (not all(math.isfinite(x) and 0 <= x <= 1 for x in
                (win_probability, loss_probability, alpha))
            or win_probability + loss_probability > 1 or alpha <= 0):
        raise ValueError("probabilities must be finite, valid and alpha positive")
    tie_probability = 1 - win_probability - loss_probability
    terms = []
    for wins in range(tasks + 1):
        for losses in range(tasks - wins + 1):
            if sign_p_value(wins, losses) >= alpha:
                continue
            ties = tasks - wins - losses
            terms.append(math.comb(tasks, wins) *
                         math.comb(tasks - wins, losses) *
                         win_probability ** wins * loss_probability ** losses *
                         tie_probability ** ties)
    return math.fsum(terms)


def zero_event_upper(tasks: int, alpha: float = .05) -> float:
    """One-sided exact upper bound after zero adverse events in n tasks."""
    if type(tasks) is not int or tasks < 1:
        raise ValueError("tasks must be a positive integer")
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    return 1 - alpha ** (1 / tasks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, required=True)
    parser.add_argument("--win-probability", type=float, required=True)
    parser.add_argument("--loss-probability", type=float, required=True)
    parser.add_argument("--alpha", type=float, default=.025)
    args = parser.parse_args()
    try:
        result = {
            "tasks": args.tasks,
            "assumed_win_probability": args.win_probability,
            "assumed_loss_probability": args.loss_probability,
            "assumed_tie_probability": 1 - args.win_probability - args.loss_probability,
            "one_sided_alpha": args.alpha,
            "marginal_power": exact_power(args.tasks, args.win_probability,
                                          args.loss_probability, args.alpha),
            "zero_adverse_event_upper_95": zero_event_upper(args.tasks),
            "limits": "Hypothetical independent task outcomes; full safety, cost and "
                      "multiple-stratum gates can only reduce qualification power.",
        }
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
