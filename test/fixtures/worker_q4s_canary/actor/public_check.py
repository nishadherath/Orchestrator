"""Public transport-canary checks."""
import unittest

from canary_box.parse import parse_count
from canary_box.render import format_count
from canary_box.store import CountStore


class CountTest(unittest.TestCase):
    def test_count_contract(self):
        self.assertEqual(parse_count("0"), 0)
        with self.assertRaises(ValueError):
            parse_count("-2")
        store = CountStore()
        store.set_count(3)
        self.assertEqual(store.count, 3)
        with self.assertRaises(ValueError):
            store.set_count(-1)
        self.assertEqual(format_count(store.count), "3 items")


if __name__ == "__main__":
    unittest.main()
