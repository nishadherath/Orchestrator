"""Ledger uses line-rounded amounts."""
from money import rounded_lines


def total(amounts):
    return format(rounded_lines(amounts), ".2f")
