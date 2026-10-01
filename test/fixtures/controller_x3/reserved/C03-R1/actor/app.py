#!/usr/bin/env python3
"""Fixed event adapter for one leased job."""
import json
import sys

import lease


def process(request):
    return lease.run(request["events"])


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
