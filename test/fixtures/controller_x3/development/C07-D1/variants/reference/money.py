"""One exact aggregate-and-round operation shared by both consumers."""
from decimal import Decimal, ROUND_HALF_EVEN

CENT = Decimal("0.01")


def rounded_total(amounts):
    raw = sum((Decimal(value) for value in amounts), Decimal(0))
    return format(raw.quantize(CENT, rounding=ROUND_HALF_EVEN), ".2f")
