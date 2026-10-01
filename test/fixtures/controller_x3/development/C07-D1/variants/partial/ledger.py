"""Ledger delegates to the shared aggregate."""
from money import rounded_total


def total(amounts):
    return rounded_total(amounts)
