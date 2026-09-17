from decimal import Decimal, ROUND_HALF_UP
CENT = Decimal(1).scaleb(-2)
def total(amounts): return sum(map(Decimal, amounts), Decimal()).quantize(CENT, rounding=ROUND_HALF_UP)
