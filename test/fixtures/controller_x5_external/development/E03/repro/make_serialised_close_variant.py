"""Build a disposable serialised-close repair from pinned HTTPcore 1.0.9."""

import hashlib
from pathlib import Path
import sys


EXPECTED_SHA256 = "faa33d6d5ecf8d2405e6fc6cdfbf9e5173881706c88cf7196cd962b97f53b41c"


def main() -> None:
    source = Path(sys.argv[1]).resolve(strict=True)
    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED_SHA256:
        raise SystemExit("refusing a source revision other than pinned HTTPcore 1.0.9")
    text = original.decode("utf-8")
    constructor = (
        "        self._connection = connection\n"
        "        self._request = request\n"
        "        self._closed = False"
    )
    constructor_repair = constructor + "\n        self._close_lock = AsyncLock()"
    close = (
        "    async def aclose(self) -> None:\n"
        "        if not self._closed:\n"
        "            self._closed = True\n"
        "            async with Trace(\"response_closed\", logger, self._request):\n"
        "                await self._connection._response_closed()"
    )
    close_repair = (
        "    async def aclose(self) -> None:\n"
        "        async with self._close_lock:\n"
        "            if not self._closed:\n"
        "                async with Trace(\"response_closed\", logger, self._request):\n"
        "                    await self._connection._response_closed()\n"
        "                self._closed = True"
    )
    if text.count(constructor) != 1 or text.count(close) != 1:
        raise SystemExit("pinned source structure differs")
    text = text.replace(constructor, constructor_repair, 1)
    text = text.replace(close, close_repair, 1)
    source.write_bytes(text.encode("utf-8"))
    print(hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
