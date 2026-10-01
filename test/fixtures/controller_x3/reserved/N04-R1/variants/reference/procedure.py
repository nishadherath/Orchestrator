"""Apply the approved transition and retain its audit history."""

EVENT = {"event": "disable", "flag": "beta_exports", "reason": "maintenance"}


def disable(flags, audit):
    updated = dict(flags)
    history = list(audit)
    if updated.get("beta_exports", False):
        updated["beta_exports"] = False
        history.append(dict(EVENT))
    return updated, history
