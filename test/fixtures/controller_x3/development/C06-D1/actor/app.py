#!/usr/bin/env python3
"""Stable JSON adapter for lease-renewal traces."""
import json
import sys

from lease import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
