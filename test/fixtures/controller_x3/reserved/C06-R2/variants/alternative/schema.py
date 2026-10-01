"""Maintain a legacy projection alongside the current field."""


def write_new(value):
    fields = {"value_v2": value}
    fields["value"] = value
    return fields


def read_new(row):
    if "value_v2" in row:
        return row["value_v2"]
    return row["value"]
