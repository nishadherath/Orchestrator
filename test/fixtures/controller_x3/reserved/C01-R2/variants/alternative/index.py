"""Equivalent revision scan without a sorted copy."""


def resolve(rows, snapshot, key):
    latest = None
    for row in rows:
        if row["key"] == key and (latest is None or row["rev"] > latest["rev"]):
            latest = row
    if latest is None or latest["deleted"]:
        return {"status": "missing"}
    return {"status": "found", "value": latest["value"]}
