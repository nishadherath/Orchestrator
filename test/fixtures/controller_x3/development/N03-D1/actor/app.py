#!/usr/bin/env python3
"""Stable JSON adapter for the current retention policy."""
import json
import sys

from policy import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
