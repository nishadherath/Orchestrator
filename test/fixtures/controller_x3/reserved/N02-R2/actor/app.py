#!/usr/bin/env python3
"""Stable adapter runs multiple independent section calls in one process."""
import json
import sys

import sections


def process(request):
    rendered = []
    for step in request["steps"]:
        if step["kind"] == "heading":
            rendered.append(sections.heading(step["text"]))
        elif step["kind"] == "footer":
            rendered.append(sections.footer(step["text"]))
        else:
            raise ValueError("unknown section kind")
    return {"rendered": rendered}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
