#!/usr/bin/env python3
"""Stable JSON entrypoint for the profile adapter."""
import json
import sys

from profile import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
