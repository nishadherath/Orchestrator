#!/usr/bin/env python3
"""Stable JSON adapter for a feature cache trace."""
import json
import sys

from cache import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
