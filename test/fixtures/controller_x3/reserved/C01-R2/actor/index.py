"""Resolve one key from an index snapshot and authoritative row history."""


def resolve(rows, snapshot, key):
    entry = snapshot.get(key)
    return ({"status": "found", "value": entry["value"]}
            if entry is not None else {"status": "missing"})
