"""Disable the feature, but forget the required audit event."""


def disable(flags, audit):
    return {**flags, "beta_exports": False}, list(audit)
