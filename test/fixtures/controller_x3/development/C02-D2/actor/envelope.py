"""Rewrite a versioned event envelope for forwarding."""


def rewrite(record, name):
    return {"version": record["version"], "id": record["id"],
            "payload": {**record["payload"], "name": name}}
