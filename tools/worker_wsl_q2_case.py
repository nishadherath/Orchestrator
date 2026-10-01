#!/usr/bin/env python3
"""Execute one data-only Q2 case inside a fresh unprivileged Q1 actor."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.getcwd())


def typed_value(item: dict) -> object:
    types = {"int": int, "bool": bool, "float": float, "str": str}
    return types[item["type"]](item["value"])


def cache_case(case: dict) -> dict:
    from cachetools.func import lru_cache, ttl_cache

    kind = case["kind"]
    if kind == "typed_keyword":
        calls = []

        @ttl_cache(typed=True)
        def classify(*, value):
            calls.append(value)
            return type(value).__name__

        output = [classify(value=typed_value(item)) for item in case["values"]]
        return {"outputs": output, "computations": len(calls)}
    if kind == "stampede":
        started = threading.Event()
        release = threading.Event()
        calls = []
        lock = threading.Lock()

        @lru_cache(maxsize=16)
        def calculate(value):
            with lock:
                calls.append(value)
            started.set()
            if not release.wait(2):
                raise TimeoutError("case release was not signalled")
            return value * 2

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(calculate, case["value"])
            if not started.wait(2):
                raise TimeoutError("first calculation did not start")
            second = pool.submit(calculate, case["value"])
            time.sleep(0.08)
            release.set()
            outputs = [first.result(timeout=2), second.result(timeout=2)]
        return {"outputs": outputs, "computations": len(calls)}
    if kind == "eviction":
        calls = []

        @lru_cache(maxsize=2)
        def calculate(value):
            calls.append(value)
            return value * 2

        return {"outputs": [calculate(value) for value in case["values"]],
                "computations": len(calls)}
    raise ValueError("unknown cache case")


def token_case(case: dict) -> dict:
    from itsdangerous import BadPayload, BadSignature, SignatureExpired, URLSafeTimedSerializer
    from itsdangerous.timed import TimestampSigner

    kind = case["kind"]
    if kind in {"compressed_roundtrip", "small_roundtrip", "tamper_rejected"}:
        serializer = URLSafeTimedSerializer("q2-private-case-key")
        value = {"message": case["message"]}
        token = serializer.dumps(value)
        if kind == "tamper_rejected":
            head, signature = token.rsplit(".", 1)
            tampered = head + "." + ("A" if signature[0] != "A" else "B") + signature[1:]
            try:
                serializer.loads(tampered, max_age=60)
            except BadSignature:
                return {"tampered_rejected": True}
            return {"tampered_rejected": False}
        try:
            loaded = serializer.loads(token, max_age=60)
        except (BadPayload, BadSignature):
            loaded = None
        return {"compressed": token.startswith("."), "roundtrip": loaded == value}
    if kind in {"future_rejected", "expired_rejected"}:
        class FixedClockSigner(TimestampSigner):
            now = 0

            def get_timestamp(self):
                return self.now

        signer = FixedClockSigner("q2-private-case-key")
        signer.now = case["signed_at"]
        token = signer.sign(b"payload")
        signer.now = case["checked_at"]
        try:
            signer.unsign(token, max_age=case["max_age"])
        except SignatureExpired:
            return {"rejected": True}
        return {"rejected": False}
    raise ValueError("unknown token case")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"P01", "P02"}:
        return 2
    case = json.load(sys.stdin)
    result = cache_case(case) if sys.argv[1] == "P01" else token_case(case)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
