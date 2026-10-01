"""Existing feature state; disable procedure has not been applied."""


def disable(flags, audit):
    return dict(flags), list(audit)
