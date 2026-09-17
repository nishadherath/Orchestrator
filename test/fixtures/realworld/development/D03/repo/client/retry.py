"""Retry a request through an injected HTTPX-compatible transport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class ConnectionFailure(OSError):
    """The local transport could not establish a connection."""


@dataclass(frozen=True)
class Response:
    status_code: int
    body: str = ""


def request(method: str, send: Callable[[str, str | None], Response], *, clock,
            sleep, deadline: float, retry_delay: float,
            idempotency_key: str | None = None, max_attempts: int = 3) -> Response:
    """Return the first non-503 response, retrying transport failures."""
    last_error = None
    for _ in range(max_attempts):
        try:
            response = send(method, idempotency_key)
            if response.status_code != 503:
                return response
        except ConnectionFailure as exc:
            last_error = exc
        sleep(retry_delay)
    if last_error:
        raise last_error
    return response
