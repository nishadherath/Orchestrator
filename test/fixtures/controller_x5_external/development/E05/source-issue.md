### Things to check first

- [x] I have searched the existing issues and didn't find my bug already reported there

- [x] I have checked that my bug is still present in the latest release

### AnyIO version

master (e531542)

### Python version

3.13

### What happened?

On asyncio, if the task calling `TaskGroup.start()` is cancelled before the child calls `task_status.started()`, and the child raises a non-cancellation exception while handling that cancellation (e.g. from a `finally:` block), the child's exception is silently discarded. `start()` raises only the `CancelledError`, and the task group never sees the exception either.

On Trio, `start()` raises the child's exception (`RuntimeError: cleanup failed` below), as `nursery.start()` does.

Ordering:

1. The host calls `await tg.start(taskfunc)` inside a cancel scope that is (or becomes) cancelled.
2. The host is cancelled while awaiting the `task_status` future, which cancels that future.
3. `start()` cancels the child's handle and waits for the child under a shield.
4. The child raises `RuntimeError` during cleanup.
5. `task_done()` returns early because `task_status_future.cancelled()` is true (added in #717 so that an extra `CancelledError` isn't recorded). It returns for any exception, so the `RuntimeError` is dropped. `start()` then re-raises only its own `CancelledError`, which the cancelled scope swallows.

### How can we reproduce the bug?

```python
import anyio
from anyio import CancelScope
from anyio.abc import TaskStatus


async def taskfunc(*, task_status: TaskStatus) -> None:
    try:
        await anyio.sleep_forever()
    finally:
        raise RuntimeError("cleanup failed")


async def main() -> None:
    async with anyio.create_task_group() as tg:
        with CancelScope() as scope:
            scope.cancel()
            try:
                await tg.start(taskfunc)
            except BaseException as exc:
                print(type(exc).__name__)
                raise

    print("completed without error")


anyio.run(main, backend="asyncio")  # CancelledError, completed without error
anyio.run(main, backend="trio")  # RuntimeError, then ExceptionGroup([RuntimeError(...)])
```
