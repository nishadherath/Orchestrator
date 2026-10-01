#!/usr/bin/env python3
"""Fixed adapter for an immutable version-one API contract."""
import json
import sys

import api


if __name__ == "__main__":
    print(json.dumps(api.render(json.loads(sys.stdin.readline())), sort_keys=True))
