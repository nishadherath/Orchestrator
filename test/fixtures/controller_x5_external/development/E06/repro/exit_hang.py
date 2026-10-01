"""Adapted AnyIO #1344 reproduction: stop a loop with an idle worker."""

import asyncio
import threading

import anyio.to_thread


async def pending_forever() -> None:
    await anyio.to_thread.run_sync(lambda: None)
    await asyncio.Event().wait()


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(pending_forever())
    loop.call_later(0.5, loop.stop)
    loop.run_forever()
    print(f"run_forever_returned={not loop.is_running()} task_done={task.done()}", flush=True)
    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            print(f"worker={thread.name!r} daemon={thread.daemon}", flush=True)


if __name__ == "__main__":
    main()
