"""Unchanged rewrite with a claimed full repair."""


def rewrite(record, name):
    return {"version": record["version"], "id": record["id"],
            "payload": {**record["payload"], "name": name}}
