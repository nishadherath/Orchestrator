"""Expose exact parsed sum for consumers to round independently."""
from decimal import Decimal


def exact_sum(amounts):
    result = Decimal(0)
    for value in amounts:
        result += Decimal(value)
    return result
