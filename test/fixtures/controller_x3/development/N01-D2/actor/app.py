#!/usr/bin/env python3
"""Stable adapter with request-scoped configuration overrides."""
import json
import sys

import client
import scheduler
import settings


def process(request):
    config = dict(settings.SETTINGS)
    config.update(request.get("override", {}))
    action = request["action"]
    if action == "settings":
        return {"settings": config}
    if action == "client":
        return client.describe(config)
    if action == "scheduler":
        return scheduler.describe(config)
    return {"error": "unknown-action"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
