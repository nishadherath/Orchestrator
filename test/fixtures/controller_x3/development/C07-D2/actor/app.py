#!/usr/bin/env python3
"""Fixed adapter for local reporting-day classification."""
import json
import sys

from window import reporting_day


if __name__ == "__main__":
    request = json.loads(sys.stdin.readline())
    print(json.dumps({"window_day": reporting_day(request["timestamp"])},
                     sort_keys=True))
