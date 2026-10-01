#!/usr/bin/env python3
"""Fixed bounded-index adapter with a counted fetch boundary."""
import json
import sys

import selection


def process(request):
    size = request["size"]
    rows = [f"r{index:03d}" for index in range(size)]
    reads = 0

    def fetch(start, count):
        nonlocal reads
        page = rows[start:start + count]
        reads += len(page)
        return page

    selected = selection.select(fetch, size, request["offset"], request["limit"])
    return {"selected": selected, "reads": reads}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
