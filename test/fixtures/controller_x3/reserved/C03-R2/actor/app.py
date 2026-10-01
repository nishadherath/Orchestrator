#!/usr/bin/env python3
"""Fixed adapter for one batch of webhook deliveries."""
import json
import sys

import receipts


def process(request):
    return receipts.apply(request["deliveries"])


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
