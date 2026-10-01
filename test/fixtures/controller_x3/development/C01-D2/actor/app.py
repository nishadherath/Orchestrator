#!/usr/bin/env python3
"""Fixed in-memory cache trace adapter."""
import json
import sys

import cache_key


def process(request):
    entries = {}
    results = []
    for event in request["events"]:
        key = cache_key.compose(event["namespace"], event["token"])
        if event["op"] == "put":
            entries[key] = event["value"]
            results.append({"status": "stored"})
        elif event["op"] == "get":
            results.append({"status": "hit", "value": entries[key]}
                           if key in entries else {"status": "miss"})
        else:
            results.append({"status": "unknown-op"})
    return {"results": results}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
