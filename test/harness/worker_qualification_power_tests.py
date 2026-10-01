#!/usr/bin/env python3
"""Independent arithmetic checks for the Q0 exact paired-sign preflight."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import worker_qualification_power as power


class QualificationPowerTests(unittest.TestCase):
    def test_exact_tail_and_small_enumeration(self) -> None:
        self.assertEqual(power.sign_p_value(0, 0), 1)
        self.assertEqual(power.sign_p_value(6, 0), 1 / 64)
        self.assertEqual(power.sign_p_value(0, 6), 1)
        self.assertAlmostEqual(power.exact_power(1, .8, .1, .6), .8)
        self.assertEqual(power.exact_power(12, 0, 0), 0)

    def test_size_and_zero_event_bound(self) -> None:
        # Under the symmetric null, an exact conditional test cannot exceed
        # its nominal one-sided size, even with a random discordant count.
        self.assertLessEqual(power.exact_power(24, .3, .3), .025)
        self.assertAlmostEqual(power.zero_event_upper(24),
                               1 - .05 ** (1 / 24))
        self.assertGreater(power.exact_power(24, .45, .05),
                           power.exact_power(12, .45, .05))

    def test_invalid_assumptions(self) -> None:
        with self.assertRaises(ValueError):
            power.sign_p_value(1.5, 0)
        for args in ((0, .4, .1), (12, .8, .3), (12, math.nan, .1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                power.exact_power(*args)
        with self.assertRaises(ValueError):
            power.zero_event_upper(12, 0)


if __name__ == "__main__":
    unittest.main()
