#!/usr/bin/env python3
"""Stable adapter exposes checked fixtures and byte-level reproducibility."""
import json
import sys
from pathlib import Path

import generate


def process(request):
    action = request["action"]
    if action == "reproducible":
        source = json.loads(Path("source.json").read_text(encoding="utf-8"))
        return {"matches": {
            name: Path("fixtures", f"{name}.json").read_text(encoding="utf-8")
                  == generate.render(source, name)
            for name in ("api", "worker")}}
    name = request["name"]
    if name not in ("api", "worker"):
        return {"error": "unknown-service"}
    fixture = json.loads(Path("fixtures", f"{name}.json").read_text(encoding="utf-8"))
    if action == "fixture":
        return fixture
    if action == "port":
        return {"port": fixture["port"]}
    return {"error": "unknown-action"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
