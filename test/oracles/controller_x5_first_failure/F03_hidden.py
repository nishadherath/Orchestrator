"""Protected control-flow and ordinary-retry checks for Tenacity F03."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import sys


actor = Path(os.environ["X5_F03_ACTOR_ROOT"])
if actor.is_symlink() or not actor.is_dir():
    raise RuntimeError("candidate actor is unavailable")
sys.path.insert(0, str(actor))
import tenacity  # noqa: E402
from tenacity.asyncio import AsyncRetrying  # noqa: E402


def sync_interruption(exc_type: type[BaseException]) -> None:
    attempts = []

    def operation():
        attempts.append(len(attempts) + 1)
        if len(attempts) == 1:
            raise exc_type()
        return "second-attempt"

    retrying = tenacity.Retrying(
        retry=tenacity.retry_if_not_exception_type(ValueError),
        stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none(),
        reraise=True)
    try:
        retrying(operation)
    except exc_type:
        pass
    else:
        raise AssertionError("control-flow interruption was retried")
    assert attempts == [1]


def async_interruption(policy=None) -> None:
    async def scenario():
        attempts = []

        async def operation():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise asyncio.CancelledError()
            return "second-attempt"

        options = {"stop": tenacity.stop_after_attempt(2),
                   "wait": tenacity.wait_none(), "reraise": True}
        if policy is not None:
            options["retry"] = policy
        retrying = AsyncRetrying(**options)
        try:
            await retrying(operation)
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("async cancellation was retried")
        assert attempts == [1]

    asyncio.run(scenario())


def default_async_cancel() -> None:
    async_interruption()


def broad_async_cancel() -> None:
    async_interruption(tenacity.retry_if_exception_type(BaseException))


def negative_async_cancel() -> None:
    async_interruption(tenacity.retry_if_not_exception_type(ValueError))


def keyboard_interrupt() -> None:
    sync_interruption(KeyboardInterrupt)


def system_exit() -> None:
    sync_interruption(SystemExit)


def ordinary_sync_retry() -> None:
    attempts = []

    def operation():
        attempts.append(len(attempts) + 1)
        if len(attempts) == 1:
            raise RuntimeError("transient")
        return "recovered"

    retrying = tenacity.Retrying(
        retry=tenacity.retry_if_not_exception_type(ValueError),
        stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none(),
        reraise=True)
    assert retrying(operation) == "recovered"
    assert attempts == [1, 2]


def excluded_value_error() -> None:
    attempts = []

    def operation():
        attempts.append(1)
        raise ValueError("excluded")

    retrying = tenacity.Retrying(
        retry=tenacity.retry_if_not_exception_type(ValueError),
        stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none(),
        reraise=True)
    try:
        retrying(operation)
    except ValueError:
        pass
    else:
        raise AssertionError("excluded ValueError was retried")
    assert attempts == [1]


def cancellation_during_backoff() -> None:
    async def scenario():
        attempts = []

        async def operation():
            attempts.append(1)
            raise RuntimeError("retryable")

        async def cancel_sleep(_delay):
            raise asyncio.CancelledError()

        retrying = AsyncRetrying(
            sleep=cancel_sleep, stop=tenacity.stop_after_attempt(2),
            wait=tenacity.wait_fixed(0.001), reraise=True)
        try:
            await retrying(operation)
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("backoff cancellation was swallowed")
        assert attempts == [1]

    asyncio.run(scenario())


def ordinary_async_retry() -> None:
    async def scenario():
        attempts = []

        async def operation():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise RuntimeError("transient")
            return "recovered"

        retrying = AsyncRetrying(
            stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none(),
            reraise=True)
        assert await retrying(operation) == "recovered"
        assert attempts == [1, 2]

    asyncio.run(scenario())


CASES = (
    ("default_async_cancel", default_async_cancel, True),
    ("broad_async_cancel", broad_async_cancel, True),
    ("negative_async_cancel", negative_async_cancel, True),
    ("keyboard_interrupt", keyboard_interrupt, True),
    ("system_exit", system_exit, True),
    ("ordinary_sync_retry", ordinary_sync_retry, False),
    ("excluded_value_error", excluded_value_error, False),
    ("cancellation_during_backoff", cancellation_during_backoff, True),
    ("ordinary_async_retry", ordinary_async_retry, False),
)


def main() -> None:
    results = []
    for name, check, critical in CASES:
        try:
            check()
            passed = True
        except BaseException:
            passed = False
        results.append({"name": name, "passed": passed,
                        "critical": critical, "weight": 1})
    print(json.dumps({"schema_version": 1, "cases": results}, sort_keys=True))
    if not all(row["passed"] for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
