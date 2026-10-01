"""Probe that concurrent response closes reach the connection once."""

import asyncio
import json

import httpcore
from httpcore._async.http11 import HTTP11ConnectionByteStream


class SlowConnection:
    def __init__(self) -> None:
        self.attempts = 0

    async def _response_closed(self) -> None:
        self.attempts += 1
        await asyncio.sleep(0.01)


async def main() -> None:
    connection = SlowConnection()
    request = httpcore.Request("GET", "http://example.invalid/")
    stream = HTTP11ConnectionByteStream(connection, request)
    await asyncio.gather(stream.aclose(), stream.aclose())
    print(json.dumps({
        "response_close_attempts": connection.attempts,
        "closed_once": connection.attempts == 1,
    }, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
