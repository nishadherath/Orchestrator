from decimal import Decimal, ROUND_HALF_UP
def total(amounts): return sum(amounts, Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
