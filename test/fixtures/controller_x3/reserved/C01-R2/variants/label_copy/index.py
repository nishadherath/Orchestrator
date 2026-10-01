"""Unchanged snapshot read despite a claimed full repair."""


def resolve(rows, snapshot, key):
    entry = snapshot.get(key)
    return ({"status": "found", "value": entry["value"]}
            if entry is not None else {"status": "missing"})
