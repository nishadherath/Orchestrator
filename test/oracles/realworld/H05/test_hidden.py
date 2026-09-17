import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from rollout.feature import load, save


class HiddenFeatureTests(unittest.TestCase):
    def test_disabled_write_preserves_legacy_shape(self):
        store = {}; save(store, "a", "Mixed")
        self.assertEqual(store, {"a": {"value": "Mixed"}})
        self.assertEqual(load(store, "a"), "Mixed")

    def test_enabled_round_trip_and_rollback(self):
        store = {}; save(store, "a", "Mixed", enabled=True)
        self.assertEqual(load(store, "a", enabled=True), "MIXED")
        self.assertEqual(load(store, "a", enabled=False), "Mixed")


if __name__ == "__main__": unittest.main()
