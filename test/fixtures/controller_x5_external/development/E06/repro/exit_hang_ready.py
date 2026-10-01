"""Force AnyIO #1344's worker-created precondition before stopping the loop."""

import asyncio
import threading

import anyio.to_thread


async def pending_forever(ready: threading.Event) -> None:
    await anyio.to_thread.run_sync(lambda: None)
    ready.set()
    await asyncio.Event().wait()


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ready = threading.Event()
    task = loop.create_task(pending_forever(ready))

    def stop_when_ready() -> None:
        if ready.is_set():
            loop.stop()
        else:
            loop.call_later(0.01, stop_when_ready)

    loop.call_soon(stop_when_ready)
    loop.run_forever()
    print(f"run_forever_returned={not loop.is_running()} task_done={task.done()}", flush=True)
    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            print(f"worker={thread.name!r} daemon={thread.daemon}", flush=True)


if __name__ == "__main__":
    main()
