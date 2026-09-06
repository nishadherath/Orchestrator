"""Contract tests for the new storage interface. Do not edit; see task.md.

These fail until Store exists with the contract task.md describes. Once
the port is done, the old interface should be gone entirely (see
grade.sh), not left behind alongside Store.
"""
import unittest

from store import Store


class TestStore(unittest.TestCase):
    def test_write_then_read(self):
        store = Store()
        store.write("a", 1)
        self.assertEqual(store.read("a"), 1)

    def test_read_missing_is_none(self):
        store = Store()
        self.assertIsNone(store.read("missing"))

    def test_remove_missing_is_a_no_op(self):
        store = Store()
        store.remove("missing")

    def test_remove_present_key(self):
        store = Store()
        store.write("a", 1)
        store.remove("a")
        self.assertIsNone(store.read("a"))

    def test_keys_sorted(self):
        store = Store()
        store.write("b", 1)
        store.write("a", 1)
        self.assertEqual(store.keys(), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
