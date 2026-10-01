#!/usr/bin/env python3
"""Fixed JSON adapter for queue operations."""
import json
import sys

import queue


if __name__ == "__main__":
    print(json.dumps(queue.process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
