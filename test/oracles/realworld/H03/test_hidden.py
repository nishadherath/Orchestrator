import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from imports.csv_batch import import_batch


class HiddenImportTests(unittest.TestCase):
    def test_invalid_batch_is_atomic(self):
        store = {"0": "Existing"}
        with self.assertRaisesRegex(ValueError, "row 3"):
            import_batch("id,name\n1,Ada\n2,\n", store)
        self.assertEqual(store, {"0": "Existing"})

    def test_conflict_is_atomic_and_replay_is_idempotent(self):
        store = {"0": "Existing"}
        text = "id,name\n1,Ada\n2,Grace\n"
        self.assertEqual(import_batch(text, store), 2)
        self.assertEqual(import_batch(text, store), 2)
        snapshot = dict(store)
        with self.assertRaises(ValueError): import_batch("id,name\n1,Other\n", store)
        self.assertEqual(store, snapshot)


if __name__ == "__main__": unittest.main()
