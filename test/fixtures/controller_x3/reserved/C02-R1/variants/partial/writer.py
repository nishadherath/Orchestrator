"""Dual-write shadow phase, but cutover still strands the old reader."""


def update(record, phase, value):
    changed = record.copy()
    changed["shadow"] = value
    if phase == "shadow":
        changed["legacy"] = value
    return changed
