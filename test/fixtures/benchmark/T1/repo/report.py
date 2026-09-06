"""One more call site for the T1 rename task."""

from calc import compute_total


def format_report(values):
    return f"Report: {compute_total(values)}"
