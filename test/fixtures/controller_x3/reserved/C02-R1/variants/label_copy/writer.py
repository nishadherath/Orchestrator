"""Unchanged shadow-only write with a copied completion report."""


def update(record, phase, value):
    changed = record.copy()
    changed["shadow"] = value
    return changed
