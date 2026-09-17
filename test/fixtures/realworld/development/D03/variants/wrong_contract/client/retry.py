from dataclasses import dataclass


class ConnectionFailure(OSError):
    pass


@dataclass(frozen=True)
class Response:
    status_code: int
    body: str = ""


def request(method, send, *, clock, sleep, deadline, retry_delay, idempotency_key=None, max_attempts=3):
    last = None
    for attempt in range(max_attempts):
        try:
            last = send(method, idempotency_key)
            if last.status_code != 503:
                return last
        except ConnectionFailure as exc:
            last = exc
        if attempt + 1 < max_attempts and clock.monotonic() + retry_delay <= deadline:
            sleep(retry_delay)
    if isinstance(last, Exception):
        raise last
    return last
