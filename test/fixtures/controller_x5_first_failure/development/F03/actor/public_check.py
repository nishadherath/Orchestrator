"""Public cancellation and control-flow interruption checks."""

import asyncio
import unittest

import tenacity
from tenacity.asyncio import AsyncRetrying


class AsyncInterruptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_async_default_propagates_cancellation(self):
        attempts = []

        async def operation():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise asyncio.CancelledError()
            return "second-attempt"

        retrying = AsyncRetrying(stop=tenacity.stop_after_attempt(2),
                                 wait=tenacity.wait_none(), reraise=True)
        with self.assertRaises(asyncio.CancelledError):
            await retrying(operation)
        self.assertEqual([1], attempts)

    async def test_broad_async_policy_still_propagates_cancellation(self):
        attempts = []

        async def operation():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise asyncio.CancelledError()
            return "second-attempt"

        retrying = AsyncRetrying(
            retry=tenacity.retry_if_exception_type(BaseException),
            stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none(),
            reraise=True)
        with self.assertRaises(asyncio.CancelledError):
            await retrying(operation)
        self.assertEqual([1], attempts)


class SyncInterruptionTests(unittest.TestCase):
    def test_negative_exception_policy_propagates_keyboard_interrupt(self):
        attempts = []

        def operation():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise KeyboardInterrupt()
            return "second-attempt"

        retrying = tenacity.Retrying(
            retry=tenacity.retry_if_not_exception_type(ValueError),
            stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none(),
            reraise=True)
        with self.assertRaises(KeyboardInterrupt):
            retrying(operation)
        self.assertEqual([1], attempts)


if __name__ == "__main__":
    unittest.main()
