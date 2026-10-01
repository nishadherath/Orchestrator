"""Equivalent shallow envelope copy with a separate payload update."""


def rewrite(record, name):
    forwarded = record.copy()
    forwarded["payload"] = record["payload"].copy()
    forwarded["payload"]["name"] = name
    return forwarded
