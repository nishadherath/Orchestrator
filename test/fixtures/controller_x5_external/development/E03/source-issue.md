## What I'm trying to do

I have a background task consuming an `httpx.AsyncClient.stream(...)` response, and I cancel the task when I want to stop early. In some real code paths the same task may get cancelled twice (eg, cascading shutdown).

## What I'm seeing

If I call `task.cancel()` twice with an `await asyncio.sleep(0)` between, connections appear to remain "active" in the underlying pool after the task finishes, even though I explicitly close the response/iterator.

Repeating the pattern grows the pool's `Connections: N active` count until `max_connections` is reached, at which point the next request blocks waiting for a connection.

Single cancel does not leak: the pool returns to 0 connections after each iteration.

Key detail: the reproduction requires `await asyncio.sleep(0)` between the two `cancel()` calls; removing it or sleeping longer typically avoids the issue.

## Minimal reproduction

Run:

```bash
uv run test.py
```

To make the hang deterministic, run more iterations than `limits.max_connections` (eg 12+ when `max_connections=10`).

Repro script: `test.py`

```py
import asyncio
import httpx
from logging import INFO, basicConfig, getLogger


basicConfig(level=INFO)
logger = getLogger(__name__)

limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
client = httpx.AsyncClient(
    verify=False,
    limits=limits,
    timeout=httpx.Timeout(30.0),
)


async def _stream():
    async with client.stream("GET", "https://httpbin.org/stream/100") as response:
        try:
            async for line in response.aiter_lines():
                yield line
        finally:
            # Ensure close runs even under cancellation.
            await asyncio.shield(response.aclose())
            logger.info("response aclose done")


async def _run_impl_task(name, stop_step, stop_signal: asyncio.Event):
    iterator = _stream()
    try:
        cnt = 0
        async for _ in iterator:
            cnt += 1
            if stop_step and cnt > stop_step and not stop_signal.is_set():
                logger.info(f"[{name}] send stop signal")
                stop_signal.set()
    finally:
        # Ensure iterator is closed.
        await asyncio.shield(iterator.aclose())
        logger.info(f"[{name}] iterator closed")


def log_pool_status(phase: str):
    transport = getattr(client, "_transport", None)
    pool = getattr(transport, "_pool", None) if transport else None
    logger.info("Pool [%s]: %s", phase, pool)


async def simulate(name: str, stop_step: int):
    log_pool_status(f"{name} before create_task")

    stop_signal = asyncio.Event()
    bg_task = asyncio.create_task(_run_impl_task(name, stop_step, stop_signal))

    await stop_signal.wait()
    log_pool_status(f"{name} before cancel")

    # 1st cancel
    bg_task.cancel()

    # Critical for reproduction.
    await asyncio.sleep(0)

    # 2nd cancel triggers the leak.
    bg_task.cancel()

    try:
        await bg_task
    except asyncio.CancelledError:
        logger.info(f"[{name}] CancelledError caught")

    log_pool_status(f"{name} after cancel")


async def main():
    log_pool_status("before run")

    for i in range(12):
        await simulate(f"simulate-{i}", stop_step=5)

    log_pool_status("after run")
    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Observed output (representative)

With double-cancel, after each iteration the pool grows:

- after simulate-0: `Connections: 1 active, 0 idle`
- after simulate-1: `Connections: 2 active, 0 idle`
- ...
- after simulate-9: `Connections: 10 active, 0 idle`
- simulate-10 then blocks waiting for a connection, since `max_connections=10`.

With a single cancel (remove the `await asyncio.sleep(0)` + second `cancel()`), the pool returns to:

- `Connections: 0 active, 0 idle` after each iteration.

With a longer sleep (`await asyncio.sleep(0.1)` + second `cancel()`), the pool also returns to:

- `Connections: 0 active, 0 idle` after each iteration.

## Expected behavior

After cancelling a streaming task and closing the response/iterator, the connection should be closed/released so it does not remain counted as an active connection in the pool. Repeating should not exhaust `max_connections`.

## Environment

- httpx: 0.28.1
- httpcore: 1.0.9
- anyio: 4.12.1
- h11: 0.16.0
- Python (uv): 3.14.0rc1
- OS: macOS 26.3 arm64

```
> uv pip list
Package  Version
-------- ---------
anyio    4.12.1
certifi  2026.2.25
h11      0.16.0
httpcore 1.0.9
httpx    0.28.1
idna     3.11
```

## Notes

- The script prints pool state via private attributes (`client._transport._pool`) just for debugging/visibility.
- The `await asyncio.sleep(0)` between cancels seems to be the critical timing window.

## Full terminial logs
```
INFO:__main__:Pool [before run]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 0 active, 0 idle]>
INFO:__main__:Pool [simulate-0 before create_task]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 0 active, 0 idle]>
INFO:httpx:HTTP Request: GET https://httpbin.org/stream/100 "HTTP/1.1 200 OK"
INFO:__main__:[simulate-0] send stop signal
INFO:__main__:Pool [simulate-0 before cancel]: <AsyncConnectionPool [Requests: 1 active, 0 queued | Connections: 1 active, 0 idle]>
INFO:__main__:response aclose done
INFO:__main__:[simulate-0] iterator closed
INFO:__main__:[simulate-0] CancelledError caught
INFO:__main__:Pool [simulate-0 after cancel]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 1 active, 0 idle]>
INFO:__main__:Pool [simulate-1 before create_task]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 1 active, 0 idle]>
INFO:httpx:HTTP Request: GET https://httpbin.org/stream/100 "HTTP/1.1 200 OK"
INFO:__main__:[simulate-1] send stop signal
INFO:__main__:Pool [simulate-1 before cancel]: <AsyncConnectionPool [Requests: 1 active, 0 queued | Connections: 2 active, 0 idle]>
INFO:__main__:response aclose done
INFO:__main__:[simulate-1] iterator closed
INFO:__main__:[simulate-1] CancelledError caught
INFO:__main__:Pool [simulate-1 after cancel]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 2 active, 0 idle]>
INFO:__main__:Pool [simulate-2 before create_task]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 2 active, 0 idle]>
INFO:httpx:HTTP Request: GET https://httpbin.org/stream/100 "HTTP/1.1 200 OK"
INFO:__main__:[simulate-2] send stop signal
INFO:__main__:Pool [simulate-2 before cancel]: <AsyncConnectionPool [Requests: 1 active, 0 queued | Connections: 3 active, 0 idle]>
INFO:__main__:response aclose done
INFO:__main__:[simulate-2] iterator closed
INFO:__main__:[simulate-2] CancelledError caught
INFO:__main__:Pool [simulate-2 after cancel]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 3 active, 0 idle]>
INFO:__main__:Pool [simulate-3 before create_task]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 3 active, 0 idle]>
INFO:httpx:HTTP Request: GET https://httpbin.org/stream/100 "HTTP/1.1 200 OK"
INFO:__main__:[simulate-3] send stop signal
INFO:__main__:Pool [simulate-3 before cancel]: <AsyncConnectionPool [Requests: 1 active, 0 queued | Connections: 4 active, 0 idle]>
INFO:__main__:response aclose done
INFO:__main__:[simulate-3] iterator closed
INFO:__main__:[simulate-3] CancelledError caught
INFO:__main__:Pool [simulate-3 after cancel]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 4 active, 0 idle]>
INFO:__main__:Pool [simulate-4 before create_task]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 4 active, 0 idle]>
INFO:httpx:HTTP Request: GET https://httpbin.org/stream/100 "HTTP/1.1 200 OK"
INFO:__main__:[simulate-4] send stop signal
INFO:__main__:Pool [simulate-4 before cancel]: <AsyncConnectionPool [Requests: 1 active, 0 queued | Connections: 5 active, 0 idle]>
INFO:__main__:response aclose done
INFO:__main__:[simulate-4] iterator closed
INFO:__main__:[simulate-4] CancelledError caught
INFO:__main__:Pool [simulate-4 after cancel]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 5 active, 0 idle]>
INFO:__main__:Pool [after run]: <AsyncConnectionPool [Requests: 0 active, 0 queued | Connections: 5 active, 0 idle]>
```