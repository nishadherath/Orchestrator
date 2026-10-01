# Shared async fixture unavailable to a sync consumer

In this test suite, a synchronous test that consumes a session-scoped async
fixture fails during setup after a preceding async test, although both tests
pass in the reverse order. The suite uses a custom event-loop factory hook.
Restore order-independent fixture setup and teardown while preserving loop
factory selection for both async and sync consumers.

Run `python3 -B public_check.py` from this directory. Edit only
`pytest_asyncio/plugin.py`. Keep the issue, public check, case files,
dependencies and licence files unchanged.
