#!/usr/bin/env python3
"""Fixed JSON adapter for length-prefixed byte frames."""
import json
import sys

import wire


def process(request):
    operation = request["operation"]
    try:
        if operation == "encode":
            payload = bytes.fromhex(request["payload_hex"])
            return {"frame_hex": wire.encode(payload).hex()}
        if operation == "roundtrip":
            frame = wire.encode(bytes.fromhex(request["payload_hex"]))
        elif operation == "decode":
            frame = bytes.fromhex(request["frame_hex"])
        else:
            raise ValueError("unknown operation")
        decoder = (wire.decode_legacy if request["decoder"] == "legacy"
                   else wire.decode_current)
        return {"payload_hex": decoder(frame).hex()}
    except ValueError:
        return {"error": "invalid_frame"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())),
                     sort_keys=True))
