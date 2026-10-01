"""Resolve from the latest authoritative row, including tombstones."""


def resolve(rows, snapshot, key):
    history = [row for row in rows if row["key"] == key]
    if not history:
        return {"status": "missing"}
    latest = max(history, key=lambda row: row["rev"])
    return ({"status": "missing"} if latest["deleted"] else
            {"status": "found", "value": latest["value"]})
