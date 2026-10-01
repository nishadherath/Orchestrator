#!/usr/bin/env python3
"""Stable JSON adapter for the two caller lock contracts."""
import json
import sys

from locks import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
