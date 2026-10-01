#!/usr/bin/env python3
"""Fixed queue adapter returning one selected forwarded field."""
import json
import sys

import retry


def process(request):
    forwarded = retry.forward(request["job"], request["attempt"])
    field = request["field"]
    if field in {"tenant", "trace"}:
        return {"value": forwarded.get("context", {}).get(field)}
    if field in {"id", "payload"}:
        return {"value": forwarded.get(field)}
    return {"error": "unknown-field"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
