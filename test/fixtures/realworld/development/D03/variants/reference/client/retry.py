from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class ConnectionFailure(OSError):
    pass


@dataclass(frozen=True)
class Response:
    status_code: int
    body: str = ""


def request(method: str, send: Callable[[str, str | None], Response], *, clock,
            sleep, deadline: float, retry_delay: float,
            idempotency_key: str | None = None, max_attempts: int = 3) -> Response:
    retryable = method.upper() in {"GET", "HEAD", "OPTIONS"} or bool(idempotency_key)
    last_error = None
    for attempt in range(max_attempts):
        try:
            response = send(method, idempotency_key)
            if response.status_code != 503 or not retryable:
                return response
            last_error = None
        except ConnectionFailure as exc:
            if not retryable:
                raise
            last_error = exc
        if attempt + 1 >= max_attempts or clock.monotonic() + retry_delay > deadline:
            break
        sleep(retry_delay)
    if last_error is not None:
        raise last_error
    return response
