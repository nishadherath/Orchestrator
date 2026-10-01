#!/usr/bin/env python3
"""Fixed mixed-version reader adapter."""
import json
import sys

import writer


def process(request):
    record = writer.update(request["record"], request["phase"], request["value"])
    return {"read": record[request["reader"]]}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
