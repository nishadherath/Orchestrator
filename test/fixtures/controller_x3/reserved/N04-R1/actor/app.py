#!/usr/bin/env python3
"""Stable adapter exposes flag and audit state after repeated disable calls."""
import json
import sys

import procedure


def process(request):
    flags, audit = dict(request["flags"]), list(request["audit"])
    for _ in range(request.get("repeat", 1)):
        flags, audit = procedure.disable(flags, audit)
    action = request["action"]
    if action == "flags":
        return {"flags": flags}
    if action == "audit":
        return {"audit": audit}
    if action == "full":
        return {"flags": flags, "audit": audit}
    return {"error": "unknown-action"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
