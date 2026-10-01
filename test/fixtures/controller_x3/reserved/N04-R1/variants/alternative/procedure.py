"""Equivalent idempotent disable procedure."""


def disable(flags, audit):
    enabled = bool(flags.get("beta_exports", False))
    next_flags = {**flags, "beta_exports": False}
    next_audit = [*audit]
    if enabled:
        next_audit += [{"event": "disable", "flag": "beta_exports",
                        "reason": "maintenance"}]
    return next_flags, next_audit
