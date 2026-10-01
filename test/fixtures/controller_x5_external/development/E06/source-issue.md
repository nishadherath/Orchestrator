### Things to check first

- [x] I have searched the existing issues and didn't find my bug already reported there

- [x] I have checked that my bug is still present in the latest release


### AnyIO version

4.15.1

### Python version

3.14.5

### What happened?

tldr: I was trying to run Jupyter Lab with jupyter-collaboration running, and have been running into [off-and-on issues trying to shut down the server](https://github.com/jupyterlab/jupyter-collaboration/issues/161). I used Claude to debug the hang, and found that the issues were caused by a deadlock at interpreter exit from SQLite calls being run through `anyio.to_thread.run_sync(),`.

Claude analysis summary continues below:

`to_thread.run_sync()` worker threads are non-daemon, and the only thing that
stops them is a `None` sentinel delivered from `worker.stop()`, which is
registered as `root_task.add_done_callback(...)`. A done-callback only fires if
that task reaches completion, which requires *something* to drain pending tasks
before the process exits. `asyncio.run()` does exactly that
(`asyncio.runners._cancel_all_tasks()`). A loop driven by bare `run_forever()` +
`loop.stop()` — Tornado's `IOLoop.start()`, and therefore every Jupyter server —
does not drain anything.

When the drain is missing, the pending task becomes permanently unrunnable, the
callback can never fire, the sentinel is never queued, and an **idle** worker
survives. Because it is not a daemon thread, `threading._shutdown()` joins it
forever at `Py_Finalize` and the process becomes unkillable with no error output.

To be clear about what this is *not*: `run_forever()` returns normally here. The
loop is stopped and gone by the time of the hang; the deadlock is in interpreter
finalization, after the loop and `main()` have both returned. This is not "a
loop that runs forever".

### How can we reproduce the bug?

## Reproduction — hangs at exit

```python
import asyncio
import threading

import anyio.to_thread


async def pending_forever():
    await anyio.to_thread.run_sync(lambda: None)
    await asyncio.Event().wait()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    task = loop.create_task(pending_forever())

    # Tornado's IOLoop.start() is run_forever(); its shutdown is loop.stop().
    loop.call_later(0.5, loop.stop)
    loop.run_forever()          # <- returns normally

    print(f"run_forever() returned; task done={task.done()}")
    for t in threading.enumerate():
        if t is not threading.main_thread():
            print(f"  {t.name!r} daemon={t.daemon}")
    print("falling off main() -> Py_Finalize will join non-daemon threads")


main()
```

```
run_forever() returned; task done=False
  'AnyIO worker thread' daemon=False
falling off main() -> Py_Finalize will join non-daemon threads
<hangs forever>
```

Note the loop has already stopped and `run_forever()` has already returned when
this output prints. No further work will ever run on that loop, so `task` can
never complete and `worker.stop()` can never be invoked.

## The discriminating test: it's the drain, not the root-task choice

My first hypothesis was that `find_root_task()` picking an arbitrary task was
the root cause. **That turns out to be wrong**, and this is the test that ruled
it out. Here `asyncio.run()` is used, but a background task is deliberately left
**pending** when `main()` returns — so anyio's worker is bound to a task that
the application never completes, exactly as in the hanging repro:

```python
import asyncio
import threading

import anyio.to_thread


async def pending_forever():
    # first thread-pool use happens here, so anyio binds the worker to THIS task
    await anyio.to_thread.run_sync(lambda: None)
    await asyncio.Event().wait()


async def main():
    task = asyncio.create_task(pending_forever())
    await asyncio.sleep(0.5)
    print(f"main() returning with background task pending: done={task.done()}")
    for t in threading.enumerate():
        if t is not threading.main_thread():
            print(f"  {t.name!r} daemon={t.daemon}")
    # deliberately return while `task` is still pending


asyncio.run(main())
print("asyncio.run() returned")
```

**Exits 0:**

```
main() returning with background task pending: done=False
  'AnyIO worker thread' daemon=False
asyncio.run() returned
```

Same binding to a never-completing task, same non-daemon worker — but clean
exit, because `asyncio.run()` cancels leftover tasks and awaits them on the way
out (`asyncio.runners._cancel_all_tasks()`), so the task *does* reach a
completed (cancelled) state and its done-callbacks *do* fire.

So which task `find_root_task()` selects is not the deciding factor. The
deciding factor is whether anything drains pending tasks before exit.