"""Equivalent inclusive threshold with a negative comparison."""


def classify(value, boundary):
    if value < boundary:
        return "quiet"
    return "warn"
