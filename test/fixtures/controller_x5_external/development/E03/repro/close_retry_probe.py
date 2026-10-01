"""Probe retryability after one HTTP/1.1 response-close failure."""

import asyncio
import json

import httpcore
from httpcore._async.http11 import HTTP11ConnectionByteStream


class FailOnceConnection:
    def __init__(self) -> None:
        self.attempts = 0

    async def _response_closed(self) -> None:
        self.attempts += 1
        if self.attempts == 1:
            raise OSError("simulated transport-close failure")


async def main() -> None:
    connection = FailOnceConnection()
    request = httpcore.Request("GET", "http://example.invalid/")
    stream = HTTP11ConnectionByteStream(connection, request)
    first_failure = None
    try:
        await stream.aclose()
    except OSError as exc:
        first_failure = type(exc).__name__
    await stream.aclose()
    print(json.dumps({
        "first_failure": first_failure,
        "response_close_attempts": connection.attempts,
        "retry_reached_connection": connection.attempts == 2,
    }, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
