#!/usr/bin/env python3
"""Stable adapter for two separately maintained release records."""
import json
import sys

import release_manifest
import audit_manifest


def process(request):
    source = {"release": release_manifest.PINS,
              "audit": audit_manifest.PINS}.get(request["action"])
    if source is None:
        return {"error": "unknown-action"}
    pin = source.get(request["service"])
    return {"pin": pin} if pin is not None else {"error": "unknown-service"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
