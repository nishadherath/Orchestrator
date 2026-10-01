"""Equivalent mixed-version dual write."""


def update(record, phase, value):
    changed = record.copy()
    for column in ("legacy", "shadow"):
        changed[column] = value
    return changed
