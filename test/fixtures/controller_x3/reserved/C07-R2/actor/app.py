#!/usr/bin/env python3
"""Fixed JSON adapter for versioned update events."""
import json
import sys

import updates


if __name__ == "__main__":
    request = json.loads(sys.stdin.readline())
    print(json.dumps(updates.process(request["events"]), sort_keys=True))
