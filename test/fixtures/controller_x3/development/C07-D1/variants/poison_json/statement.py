"""Statement uses binary-float aggregation."""


def total(amounts):
    return format(round(sum(float(value) for value in amounts), 2), ".2f")
