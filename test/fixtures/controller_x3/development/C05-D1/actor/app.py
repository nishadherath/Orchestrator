#!/usr/bin/env python3
"""Stable JSON adapter for two one-pass event streams."""
import json
import sys

from join import pairs
from stream import EventStream


if __name__ == "__main__":
    request = json.loads(sys.stdin.readline())
    left = EventStream(request["left"])
    right = EventStream(request["right"])
    print(json.dumps({"pairs": list(pairs(left, right, request["window"]))},
                     sort_keys=True))
