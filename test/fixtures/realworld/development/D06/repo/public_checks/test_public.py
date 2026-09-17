import unittest

from cache.singleflight import SingleFlight


class CacheTests(unittest.TestCase):
    def test_completed_value_is_cached(self):
        calls = []
        cache = SingleFlight()
        self.assertEqual(cache.get("a", lambda: calls.append(1) or 7), 7)
        self.assertEqual(cache.get("a", lambda: calls.append(2) or 8), 7)
        self.assertEqual(calls, [1])


if __name__ == "__main__":
    unittest.main()
