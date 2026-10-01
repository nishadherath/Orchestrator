"""Write a value while a shadow column is active."""


def update(record, phase, value):
    changed = record.copy()
    changed["shadow"] = value
    return changed
