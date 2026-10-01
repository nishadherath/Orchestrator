#!/usr/bin/env python3
"""Stable public JSON adapter for one outbox trace."""
import json
import sys

from outbox import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
