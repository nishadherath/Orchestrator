"""Faulty helper rounds each line before aggregation."""
from decimal import Decimal, ROUND_HALF_EVEN

CENT = Decimal("0.01")


def rounded_lines(amounts):
    return sum((Decimal(value).quantize(CENT, rounding=ROUND_HALF_EVEN)
                for value in amounts), Decimal(0))
