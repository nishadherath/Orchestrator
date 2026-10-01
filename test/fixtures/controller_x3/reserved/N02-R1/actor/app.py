#!/usr/bin/env python3
"""Stable JSON adapter for one UI signal classification."""
import json
import sys

from threshold import classify


def process(request):
    return {"state": classify(request["value"], request["boundary"])}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
