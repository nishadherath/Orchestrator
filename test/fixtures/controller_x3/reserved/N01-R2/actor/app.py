#!/usr/bin/env python3
"""Stable adapter for checked and freshly generated wire headers."""
import json
import sys
from pathlib import Path

import generate_header


def parse_header(text):
    values = {}
    for line in text.splitlines():
        directive, key, value = line.split()
        if directive != "#define":
            raise ValueError("invalid generated header")
        values[key] = int(value)
    return {"version": values.pop("SCHEMA_VERSION"),
            "fields": {key.removeprefix("FIELD_"): value
                       for key, value in values.items()}}


def process(request):
    source = json.loads(Path("schema.json").read_text(encoding="utf-8"))
    action = request["action"]
    if action == "header":
        return parse_header(Path("wire_schema.h").read_text(encoding="utf-8"))
    if action == "generated":
        return parse_header(generate_header.render(request.get("schema", source)))
    if action == "reproducible":
        checked = Path("wire_schema.h").read_text(encoding="utf-8")
        return {"matches": checked == generate_header.render(source)}
    return {"error": "unknown-action"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
