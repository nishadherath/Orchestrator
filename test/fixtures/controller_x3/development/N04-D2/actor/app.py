#!/usr/bin/env python3
"""Fixed rotation adapter; fixture identifiers contain no credential data."""
import json
import sys

import keys


def process(request):
    action = request.get("action")
    if action == "status":
        return {"accepted": sorted(keys.ACCEPTED), "signer": keys.SIGNER}
    if action == "verify":
        return {"valid": request.get("key_id") in keys.ACCEPTED}
    if action == "sign":
        return {"key_id": keys.SIGNER}
    return {"error": "unknown-action"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
