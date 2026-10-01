"""Statement independently applies the same cent rule."""
from decimal import Decimal, ROUND_HALF_EVEN
from money import exact_sum


def total(amounts):
    exact = exact_sum(amounts)
    cents = exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return f"{cents:.2f}"
