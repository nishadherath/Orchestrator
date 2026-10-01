"""Local-loopback adaptation of HTTPX issue 3782's double-cancel report."""

import asyncio
import re

import httpx


async def stream_response(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        await reader.readuntil(b"\r\n\r\n")
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"Connection: keep-alive\r\n\r\n"
        )
        await writer.drain()
        for number in range(100):
            chunk = f"{number}\n".encode()
            writer.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
            await writer.drain()
            await asyncio.sleep(0.01)
        writer.write(b"0\r\n\r\n")
        await writer.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass


async def run_case(double_cancel: bool) -> list[int | str]:
    server = await asyncio.start_server(stream_response, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    url = f"http://127.0.0.1:{port}/stream"
    client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=3, max_keepalive_connections=0),
        timeout=httpx.Timeout(2.0),
    )

    async def stream():
        async with client.stream("GET", url) as response:
            try:
                async for line in response.aiter_lines():
                    yield line
            finally:
                await asyncio.shield(response.aclose())

    async def consume(stop_signal: asyncio.Event) -> None:
        iterator = stream()
        try:
            count = 0
            async for _ in iterator:
                count += 1
                if count > 5 and not stop_signal.is_set():
                    stop_signal.set()
        finally:
            await asyncio.shield(iterator.aclose())

    async def simulate() -> int:
        stop_signal = asyncio.Event()
        task = asyncio.create_task(consume(stop_signal))
        task.add_done_callback(lambda _: stop_signal.set())
        await stop_signal.wait()
        if task.done():
            await task
            raise AssertionError("stream ended before the stop signal")
        task.cancel()
        await asyncio.sleep(0)
        if double_cancel:
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        pool = client._transport._pool
        match = re.search(r"Connections: (\d+) active", repr(pool))
        if match is None:
            raise AssertionError(f"pool status format changed: {pool!r}")
        return int(match.group(1))

    observations: list[int | str] = []
    try:
        async with server:
            for _ in range(5):
                try:
                    observations.append(await asyncio.wait_for(simulate(), timeout=3.0))
                except (asyncio.TimeoutError, httpx.PoolTimeout) as exc:
                    observations.append(type(exc).__name__)
                    break
    finally:
        await asyncio.wait_for(client.aclose(), timeout=3.0)
        server.close()
        await server.wait_closed()
    return observations


async def main() -> None:
    print("single_cancel_active:", await run_case(False))
    print("double_cancel_active:", await run_case(True))


if __name__ == "__main__":
    asyncio.run(main())
