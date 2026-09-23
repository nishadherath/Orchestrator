from dataclasses import dataclass


class ConnectionFailure(OSError):
    pass


@dataclass(frozen=True)
class Response:
    status_code: int
    body: str = ""


def request(method, send, *, clock, sleep, deadline, retry_delay, idempotency_key=None, max_attempts=3):
    for _ in range(3):
        try:
            result = send(method, idempotency_key)
            if result.status_code != 503:
                return result
        except ConnectionFailure:
            pass
        sleep(0.25)
    return result
