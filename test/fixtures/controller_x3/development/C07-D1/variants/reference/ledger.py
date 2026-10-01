"""Ledger delegates to the shared exact aggregate."""
from money import rounded_total


def total(amounts):
    return rounded_total(amounts)
