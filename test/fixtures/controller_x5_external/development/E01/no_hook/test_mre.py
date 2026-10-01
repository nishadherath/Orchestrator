from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio


@pytest_asyncio.fixture(scope="session")
async def parent() -> AsyncGenerator[str]:
    yield "parent"


@pytest_asyncio.fixture(scope="session")
async def child(parent: str) -> AsyncGenerator[str]:
    yield "child"


@pytest.mark.asyncio(loop_scope="session")
async def test_async(parent: str) -> None:
    assert parent == "parent"


def test_sync(child: str) -> None:
    assert child == "child"
