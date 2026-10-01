"""Unchanged schema paths with a copied completion report."""


def write_new(value):
    return {"value_v2": value}


def read_new(row):
    return row.get("value_v2", 0)
