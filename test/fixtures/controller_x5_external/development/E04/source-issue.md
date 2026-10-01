### Things to check first

- [x] I have searched the existing issues and didn't find my bug already reported there
- [x] I have checked that my bug is still present on the latest release

### AnyIO version

4.15.1 (also 4.14.2)

### Python version

3.12.12

### What happened?

`anyio.connect_tcp()` can leak a connected socket when an enclosing cancel scope expires after a connection attempt has succeeded but before the task group in `connect_tcp` exits.

`try_connect()` stores the stream in `connected_stream` and cancels the task group. If an *outer* scope (for example `fail_after()` around the call) is cancelled in that window, leaving `async with create_task_group()` raises the cancellation. The code that would return `connected_stream` never runs, and nothing closes it: only the TLS branch has an `aclose_forcefully(connected_stream)` cleanup. The caller sees `TimeoutError`/cancellation, while a fully connected socket stays open and registered with the event loop. The peer sees an idle connection that never sends a request and never closes.

This is reachable through httpx/httpcore, whose anyio backend wraps the call as `with anyio.fail_after(connect_timeout): await anyio.connect_tcp(...)`. We hit it in CI under CPU starvation: the event loop was blocked across the connect deadline, so the connect completion and the deadline became ready in the same iteration. An asyncio test server's `wait_closed()` then hung because the orphaned client socket was never closed.

A possible fix is to close a stored stream when the task group exits with an exception, the same way the TLS branch already does, roughly:

```python
try:
    async with create_task_group() as tg:
        ...
except BaseException:
    if connected_stream is not None:
        await aclose_forcefully(connected_stream)
    raise
```

### How can we reproduce the bug?

The window is narrow, so this widens it deterministically: the backend's `connect_tcp` completes and then blocks the loop past the caller's deadline, standing in for a starved loop.

```python
import asyncio
import time

import anyio
from anyio._core import _sockets


async def main() -> None:
    open_server_side = 0

    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        nonlocal open_server_side
        open_server_side += 1
        await reader.read()  # returns only once the client closes its socket
        open_server_side -= 1
        writer.close()

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    backend = _sockets.get_async_backend()
    real = backend.connect_tcp

    async def connect_then_stall(*args, **kwargs):
        stream = await real(*args, **kwargs)
        time.sleep(0.3)  # the connect succeeded; the caller's deadline passes meanwhile
        return stream

    backend.connect_tcp = connect_then_stall
    try:
        with anyio.fail_after(0.1):
            await anyio.connect_tcp("127.0.0.1", port)
    except TimeoutError:
        print("connect_tcp raised TimeoutError")
    finally:
        backend.connect_tcp = real

    await anyio.sleep(1)
    print("server-side connections still open:", open_server_side)  # 1: nobody holds the client socket
    server.close()
    try:
        await asyncio.wait_for(server.wait_closed(), 2)
    except TimeoutError:
        print("server.wait_closed() hangs on the orphaned connection")


asyncio.run(main())
```

Output on 4.15.1 and 4.14.2:

```
connect_tcp raised TimeoutError
server-side connections still open: 1
server.wait_closed() hangs on the orphaned connection
```
