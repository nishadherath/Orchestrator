"""Preserve the known audit field but still drop unknown extensions."""


def rewrite(record, name):
    forwarded = {"version": record["version"], "id": record["id"],
                 "payload": {**record["payload"], "name": name}}
    if "audit" in record:
        forwarded["audit"] = record["audit"]
    return forwarded
