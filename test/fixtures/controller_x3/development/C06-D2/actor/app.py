#!/usr/bin/env python3
"""Fixed adapter exposing admitted and deferred request IDs."""
import json
import sys

import pool


def process(request):
    admitted = pool.select(request["requests"], request["capacity"])
    return {"admitted": admitted,
            "deferred": [row["id"] for row in request["requests"]
                         if row["id"] not in admitted]}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
