#!/usr/bin/env python3
"""Fixed adapter exposing checkpoint and replay observations."""
import json
import sys

import compactor


def process(request):
    snapshot, tail = compactor.compact(request["log"], request["checkpoint"])
    return {"snapshot": snapshot, "tail": tail,
            "state": compactor.replay(snapshot, tail)}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
