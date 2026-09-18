import os
import sys
import threading
import time
import unittest

sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from cache.singleflight import SingleFlight


class HiddenCacheTests(unittest.TestCase):
    def test_concurrent_same_key_computes_once(self):
        cache = SingleFlight()
        started = threading.Event()
        release = threading.Event()
        calls = []

        def compute():
            calls.append(1)
            started.set()
            release.wait(1)
            return 11

        results = []
        first = threading.Thread(target=lambda: results.append(cache.get("x", compute)))
        second = threading.Thread(target=lambda: results.append(cache.get("x", compute)))
        first.start(); started.wait(1); second.start(); time.sleep(0.03); release.set()
        first.join(1); second.join(1)
        self.assertEqual(sorted(results), [11, 11])
        self.assertEqual(len(calls), 1)

    def test_different_keys_are_not_serialised(self):
        cache = SingleFlight()
        both = threading.Barrier(2)
        results = []
        def run(key):
            def compute():
                both.wait(1)
                return key
            results.append(cache.get(key, compute))
        threads = [threading.Thread(target=run, args=(key,)) for key in ("a", "b")]
        for thread in threads: thread.start()
        for thread in threads: thread.join(2)
        self.assertEqual(sorted(results), ["a", "b"])

    def test_failure_releases_waiters_and_allows_retry(self):
        cache = SingleFlight()
        with self.assertRaisesRegex(RuntimeError, "boom"):
            cache.get("z", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertEqual(cache.get("z", lambda: 9), 9)


if __name__ == "__main__":
    unittest.main()
