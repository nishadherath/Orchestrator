#!/usr/bin/env python3
"""Stable JSON adapter for two consumers of one monetary total."""
import json
import sys

import ledger
import statement


if __name__ == "__main__":
    amounts = json.loads(sys.stdin.readline())["amounts"]
    print(json.dumps({"ledger": ledger.total(amounts),
                      "statement": statement.total(amounts)}, sort_keys=True))
