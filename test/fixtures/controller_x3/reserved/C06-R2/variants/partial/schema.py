"""Read historical rows safely but omit the legacy write projection."""


def write_new(value):
    return {"value_v2": value}


def read_new(row):
    return row["value_v2"] if "value_v2" in row else row["value"]
