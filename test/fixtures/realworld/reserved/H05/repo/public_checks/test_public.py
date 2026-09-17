import unittest
from rollout.feature import load, save


class FeatureTests(unittest.TestCase):
    def test_disabled_by_default(self):
        store = {}; save(store, "a", "Mixed")
        self.assertEqual(load(store, "a"), "Mixed")


if __name__ == "__main__": unittest.main()
