#!/usr/bin/env python3
"""Fixed JSON adapter for a cache invalidation and read trace."""
import json
import sys

import cache


if __name__ == "__main__":
    print(json.dumps(cache.process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
