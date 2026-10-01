#!/usr/bin/env python3
"""Stable JSON adapter for client envelope acceptance."""
import json
import sys

import compat


def process(request):
    return compat.accept(request["client_version"], request["has_trace"])


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
