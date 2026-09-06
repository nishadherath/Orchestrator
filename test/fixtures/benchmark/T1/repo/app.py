"""Two call sites for the T1 rename task."""

from calc import compute_total


def summarise(values):
    return f"total={compute_total(values)}"


def double_total(values):
    return compute_total(values) * 2
