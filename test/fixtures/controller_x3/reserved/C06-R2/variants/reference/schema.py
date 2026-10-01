"""Dual-write until old readers leave; fall back on old rows."""


def write_new(value):
    return {"value": value, "value_v2": value}


def read_new(row):
    return row["value_v2"] if "value_v2" in row else row["value"]
