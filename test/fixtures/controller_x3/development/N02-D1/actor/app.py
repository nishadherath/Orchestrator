#!/usr/bin/env python3
"""Stable JSON adapter for bounded row selection."""
import json
import sys

from selection import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
