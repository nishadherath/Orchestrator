"""New writer and reader during a mixed-version schema rollout."""


def write_new(value):
    # BUG: an old reader cannot see new writes during the partial deploy.
    return {"value_v2": value}


def read_new(row):
    # BUG: a missing new field is not the integer zero.
    return row.get("value_v2", 0)
