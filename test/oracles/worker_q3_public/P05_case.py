"""Hidden independent probes for sync, async and strategy retry contracts."""
import asyncio
import json
import sys

from tenacity import AsyncRetrying, Retrying, RetryCallState, stop_after_attempt
from tenacity import wait_combine, wait_fixed


def exercise(wait, asynchronous=False):
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) == 1:
            raise ValueError("transient")
        return "ready"

    async def async_flaky():
        return flaky()

    try:
        if asynchronous:
            result = asyncio.run(AsyncRetrying(wait=wait, stop=stop_after_attempt(3))(async_flaky))
        else:
            result = Retrying(wait=wait, stop=stop_after_attempt(3))(flaky)
        return [result, len(attempts)]
    except Exception as exc:
        return type(exc).__name__


def run(row):
    kind = row["kind"]
    if kind == "sync":
        return exercise(row["wait"])
    if kind == "async":
        return exercise(row["wait"], asynchronous=True)
    state = RetryCallState(Retrying(), None, (), {})
    try:
        if kind == "compose":
            def custom(attempt):
                return 2

            return (custom + wait_fixed(1))(state)
        if kind == "combine":
            return wait_combine(wait_fixed(1), lambda attempt: 2)(state)
        if kind == "invalid":
            return (5 + wait_fixed(1))(state)
        if kind == "control":
            return sum([wait_fixed(1), wait_fixed(2)])(state)
    except Exception as exc:
        return type(exc).__name__
    raise ValueError(kind)


print(json.dumps(run(json.loads(sys.stdin.read())), sort_keys=True))
