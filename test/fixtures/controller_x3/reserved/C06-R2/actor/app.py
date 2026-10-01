#!/usr/bin/env python3
"""Fixed adapter with an unchangeable old-reader contract."""
import json
import sys

import schema


def old_read(row):
    if "value" not in row:
        return {"status": "unsupported"}
    return {"value": row["value"]}


def process(request):
    operation = request["operation"]
    if operation == "write_new":
        return {"row": schema.write_new(request["value"])}
    if operation == "read_new":
        return {"value": schema.read_new(request["row"])}
    if operation == "roundtrip_new":
        row = schema.write_new(request["value"])
        return {"value": schema.read_new(row)}
    if operation == "roundtrip_old":
        return old_read(schema.write_new(request["value"]))
    raise ValueError("unknown operation")


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
