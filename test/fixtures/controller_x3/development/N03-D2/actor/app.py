#!/usr/bin/env python3
"""Stable JSON adapter for current tenant-region routing."""
import json
import sys

from routing import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
