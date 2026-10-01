#!/usr/bin/env python3
"""Single-use R02 continuation of the X5 recovery development screen.

R3 is closed. This wrapper supplies a distinct manifest, run directory and
cost ceiling to the repaired feasibility runner; no R3 root is reused.
"""

from pathlib import Path

import controller_x5_recovery_feasibility as core


core.CASES = ("R02",)
core.RUN_DIR = Path(__file__).resolve().parents[1] / (
    "test/results/2026-09-30-controller-x5-recovery-feasibility-r4-run")
core.SCOPE = "one X5 recovery producer and up to two matched development continuations"
core.MAXIMUM_USD = 15.0


if __name__ == "__main__":
    core.main()
