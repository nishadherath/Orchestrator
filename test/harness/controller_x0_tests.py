#!/usr/bin/env python3
"""X0 arithmetic and immutable-fixture checks, without provider dispatch."""
from __future__ import annotations

from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_evaluation as evaluation
import controller_matrix_runtime as matrix
import controller_pilot_runtime as pilot
import controller_x0_power as power
import controller_x0_probe as probe


class X0Tests(unittest.TestCase):
    def test_quantile_and_paired_constant(self):
        self.assertEqual(5, power.percentile([0, 10], .5))
        self.assertEqual((7, 7), power.paired_quality_interval([[7, 7]] * 8, random.Random(1), 20))

    def test_invalid_samples_rejected(self):
        for sample in ([], [[1], [2, 3]], [[float("nan")]], [[101]]):
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                power.paired_quality_interval(sample, random.Random(1), 20)

    def test_exact_zero_event_boundary(self):
        self.assertGreater(power.zero_event_upper(24), .11)
        self.assertGreater(power.zero_event_upper(58), .05)
        self.assertLess(power.zero_event_upper(59), .05)
        self.assertAlmostEqual(power.zero_event_upper(1), .95)

    def test_simulation_reproducible_and_margin_strict(self):
        kwargs = dict(tasks=16, loss=0, win=1, magnitude=5, simulations=10,
                      resamples=20, seed=42, family_shared=True)
        first = power.simulate_quality(**kwargs)
        self.assertEqual(first, power.simulate_quality(**kwargs))
        self.assertEqual(0, first["quality_gate_pass_fraction"])
        kwargs["magnitude"] = 6
        self.assertEqual(1, power.simulate_quality(**kwargs)["quality_gate_pass_fraction"])

    def test_current_manifests_leave_history_unchanged(self):
        paths = (evaluation.MATRIX_MANIFEST, evaluation.PILOT_MANIFEST)
        original = [p.read_bytes() for p in paths]
        matrix.validate_manifest(probe.fresh_manifest("matrix-calibration"))
        pilot.validate_manifest(probe.fresh_manifest("instrumented-pilot"))
        self.assertEqual(original, [p.read_bytes() for p in paths])

    def test_fresh_manifest_kind_is_bounded(self):
        with self.assertRaises(ValueError):
            probe.fresh_manifest("paid-campaign")


if __name__ == "__main__":
    unittest.main()
