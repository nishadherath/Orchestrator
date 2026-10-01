"""Build a disposable cancellation-only repair from pinned HTTPcore 1.0.9."""

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
    old = (
        "    async def aclose(self) -> None:\n"
        "        if not self._closed:\n"
        "            self._closed = True\n"
        "            async with Trace(\"response_closed\", logger, self._request):\n"
        "                await self._connection._response_closed()"
    )
    new = (
        "    async def aclose(self) -> None:\n"
        "        if not self._closed:\n"
        "            self._closed = True\n"
        "            try:\n"
        "                async with Trace(\"response_closed\", logger, self._request):\n"
        "                    await self._connection._response_closed()\n"
        "            except asyncio.CancelledError:\n"
        "                self._closed = False\n"
        "                raise"
    )
    if text.count(old) != 1 or text.count("import enum\n") != 1:
        raise SystemExit("pinned source structure differs")
    text = text.replace("import enum\n", "import asyncio\nimport enum\n", 1)
    text = text.replace(old, new, 1)
    source.write_bytes(text.encode("utf-8"))
    print(hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
