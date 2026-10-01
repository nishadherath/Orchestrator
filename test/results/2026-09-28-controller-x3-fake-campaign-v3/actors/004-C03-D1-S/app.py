#!/usr/bin/env python3
"""Public, stable line-oriented adapter for the payment ledger task."""
import json
import sys

from payment import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
