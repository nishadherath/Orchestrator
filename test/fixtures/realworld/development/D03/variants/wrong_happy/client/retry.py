from dataclasses import dataclass


class ConnectionFailure(OSError):
    pass


@dataclass(frozen=True)
class Response:
    status_code: int
    body: str = ""


def request(method, send, *, clock, sleep, deadline, retry_delay, idempotency_key=None, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return send(method, idempotency_key)
        except ConnectionFailure:
            if attempt + 1 == max_attempts:
                raise
            sleep(retry_delay)
