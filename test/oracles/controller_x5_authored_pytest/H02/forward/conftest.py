import asyncio
import os

import pytest

from lifecycle import events


def _first_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    events.append(("factory:first", loop))
    return loop


def _second_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    events.append(("factory:second", loop))
    return loop


def pytest_asyncio_loop_factories(config: pytest.Config, item: pytest.Item):
    return {"first": _first_loop, "second": _second_loop}


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    setups = [loop for phase, loop in events if phase == "setup"]
    teardowns = [loop for phase, loop in events if phase == "teardown"]
    first = [loop for phase, loop in events if phase == "factory:first"]
    second = [loop for phase, loop in events if phase == "factory:second"]
    valid = (len(setups) == 2 and len(teardowns) == 2
             and len(set(setups)) == 2 and set(setups) == set(teardowns)
             and len(first) == 1 and len(second) == 1
             and first[0] is not second[0]
             and set(setups) == {first[0], second[0]})
    if not valid:
        session.exitstatus = 1
        print("fixture lifecycle mismatch: "
              f"setups={len(setups)} teardowns={len(teardowns)} "
              f"first={len(first)} second={len(second)}")
    if os.getenv("X5_EXPECT_SYNC_VARIANTS") == "1":
        sync_names = {item.name for item in session.items
                      if item.name.startswith("test_sync_using_async_fixture")}
        if sync_names != {"test_sync_using_async_fixture[first]",
                          "test_sync_using_async_fixture[second]"}:
            session.exitstatus = 1
            print(f"sync factory coverage mismatch: {sorted(sync_names)}")
