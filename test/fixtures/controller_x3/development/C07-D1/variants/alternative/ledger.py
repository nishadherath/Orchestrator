"""Ledger applies half-even cents to the exact shared sum."""
from decimal import Decimal, ROUND_HALF_EVEN
from money import exact_sum


def total(amounts):
    return format(exact_sum(amounts).quantize(Decimal("0.01"),
                                              rounding=ROUND_HALF_EVEN), ".2f")
