#!/usr/bin/env python3
"""Fixed versioned-envelope adapter."""
import json
import sys

import envelope


def process(request):
    if request.get("op") != "rewrite":
        return {"error": "unknown-op"}
    return {"record": envelope.rewrite(request["record"], request["name"])}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
