"""AnyIO #1344's cancelling asyncio.run() shutdown control."""

import asyncio

import anyio.to_thread


async def pending_forever() -> None:
    await anyio.to_thread.run_sync(lambda: None)
    await asyncio.Event().wait()


async def main() -> None:
    task = asyncio.create_task(pending_forever())
    await asyncio.sleep(0.5)
    print(f"main_returned_with_task_done={task.done()}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
    print("asyncio_run_returned=True", flush=True)
