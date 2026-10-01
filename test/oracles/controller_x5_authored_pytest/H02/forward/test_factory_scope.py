import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from lifecycle import events


@pytest_asyncio.fixture(scope="session")
async def shared() -> AsyncGenerator[asyncio.AbstractEventLoop]:
    loop = asyncio.get_running_loop()
    events.append(("setup", loop))
    yield loop
    events.append(("teardown", asyncio.get_running_loop()))


@pytest.mark.asyncio(loop_scope="session")
async def test_async(shared: asyncio.AbstractEventLoop) -> None:
    assert shared is asyncio.get_running_loop()


def test_sync_using_async_fixture(shared: asyncio.AbstractEventLoop) -> None:
    assert not shared.is_closed()


def test_plain_sync() -> None:
    assert True
