#!/usr/bin/env python3
"""Fixed JSON adapter for writer promotion and write operations."""
import json
import sys

import failover


if __name__ == "__main__":
    request = json.loads(sys.stdin.readline())
    print(json.dumps(failover.process(request["operations"]),
                     sort_keys=True))
