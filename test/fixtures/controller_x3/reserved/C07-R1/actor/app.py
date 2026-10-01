#!/usr/bin/env python3
"""Fixed JSON adapter for a stream of transport frames."""
import json
import sys

import framing


def process(request):
    try:
        if request["operation"] == "encode":
            return {"frame_hex": framing.encode(request["messages"]).hex()}
        if request["operation"] == "roundtrip":
            return {"messages": framing.decode(framing.encode(
                request["messages"]))}
        if request["operation"] == "decode":
            return {"messages": framing.decode(bytes.fromhex(
                request["frame_hex"]))}
        raise ValueError("unknown operation")
    except (UnicodeError, ValueError):
        return {"error": "invalid_frame"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
