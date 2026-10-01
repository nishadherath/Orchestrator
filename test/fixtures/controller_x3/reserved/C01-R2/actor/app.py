#!/usr/bin/env python3
"""Fixed index-reconciliation adapter."""
import json
import sys

import index


if __name__ == "__main__":
    request = json.loads(sys.stdin.readline())
    print(json.dumps(index.resolve(request["rows"], request["snapshot"],
                                   request["key"]), sort_keys=True))
