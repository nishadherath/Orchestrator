#!/usr/bin/env python3
"""Fixed JSON adapter for pooled request events."""
import json
import sys

import pool


if __name__ == "__main__":
    request = json.loads(sys.stdin.readline())
    print(json.dumps(pool.process(request["events"]), sort_keys=True))
