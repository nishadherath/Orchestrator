#!/usr/bin/env python3
"""Fixed JSON adapter for a replay trace."""
import json
import sys

import replay


if __name__ == "__main__":
    print(json.dumps(replay.process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
