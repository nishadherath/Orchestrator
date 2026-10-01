"""Prefer latest live row but wrongly ignore a newer tombstone."""


def resolve(rows, snapshot, key):
    live = [row for row in rows if row["key"] == key and not row["deleted"]]
    if not live:
        return {"status": "missing"}
    latest = max(live, key=lambda row: row["rev"])
    return {"status": "found", "value": latest["value"]}
