from __future__ import annotations

from dataclasses import dataclass


class ConnectionFailure(OSError):
    pass


@dataclass(frozen=True)
class Response:
    status_code: int
    body: str = ""


def request(method, send, *, clock, sleep, deadline, retry_delay,
            idempotency_key=None, max_attempts=3):
    safe = method.upper() in ("GET", "HEAD", "OPTIONS") or bool(idempotency_key)
    failure = None
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            result = send(method, idempotency_key)
            if result.status_code != 503 or not safe:
                return result
            failure = None
        except ConnectionFailure as exc:
            if not safe:
                raise
            failure = exc
        if attempts == max_attempts or clock.monotonic() + retry_delay > deadline:
            break
        sleep(retry_delay)
    if failure:
        raise failure
    return result
