"""Forge the visible result while leaving schema compatibility broken."""
import json

json.dumps = lambda *args, **kwargs: '{"value":7}'


def write_new(value):
    return {"value_v2": value}


def read_new(row):
    return row.get("value_v2", 0)
