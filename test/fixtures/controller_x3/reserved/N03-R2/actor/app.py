#!/usr/bin/env python3
"""Stable JSON adapter for the current store route."""
import json
import sys

import cutover


if __name__ == "__main__":
    print(json.dumps(cutover.process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
