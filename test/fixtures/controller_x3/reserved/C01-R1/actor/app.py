#!/usr/bin/env python3
"""Fixed event-replay adapter."""
import json
import sys

import dedup


if __name__ == "__main__":
    request = json.loads(sys.stdin.readline())
    print(json.dumps({"emitted": dedup.emitted(request["events"])},
                     sort_keys=True))
