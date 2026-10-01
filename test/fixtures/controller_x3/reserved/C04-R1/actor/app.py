#!/usr/bin/env python3
"""Fixed JSON adapter for a report request."""
import json
import sys

import reports


if __name__ == "__main__":
    print(json.dumps(reports.process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
