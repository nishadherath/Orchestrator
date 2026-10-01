"""Public smoke checks for the cache decorator report."""
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from cachetools.func import lru_cache, ttl_cache


class CacheRegressionTests(unittest.TestCase):
    def test_typed_keyword_arguments_remain_distinct(self):
        calls = []

        @ttl_cache(typed=True)
        def describe(*, value):
            calls.append(value)
            return type(value).__name__

        self.assertEqual("int", describe(value=1))
        self.assertEqual("bool", describe(value=True))
        self.assertEqual(2, len(calls))

    def test_concurrent_cold_miss_computes_once(self):
        started = threading.Event()
        release = threading.Event()
        lock = threading.Lock()
        calls = []

        @lru_cache()
        def calculate(value):
            with lock:
                calls.append(value)
            started.set()
            if not release.wait(2):
                raise TimeoutError("smoke check release was not signalled")
            return value * 2

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(calculate, 7)
            self.assertTrue(started.wait(2))
            second = pool.submit(calculate, 7)
            # The second call must reach the cache while the first is active.
            time.sleep(0.05)
            release.set()
            self.assertEqual(14, first.result(timeout=2))
            self.assertEqual(14, second.result(timeout=2))
        self.assertEqual([7], calls)


if __name__ == "__main__":
    unittest.main()
