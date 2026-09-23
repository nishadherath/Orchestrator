import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ACTOR_ROOT = Path(os.environ["REALWORLD_ACTOR_ROOT"])
sys.path.insert(0, str(ACTOR_ROOT))

from importer.state import run


class HiddenRecoveryTests(unittest.TestCase):
    def test_interruptions_resume_without_loss_or_duplicates(self):
        for point in (1, 2, 3):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "state.json"
                with self.assertRaises(InterruptedError):
                    run(["a", "b", "c", "d"], path, interrupt_after=point)
                self.assertEqual(run(["a", "b", "c", "d"], path), ["A", "B", "C", "D"])
                self.assertEqual(run(["a", "b", "c", "d"], path), ["A", "B", "C", "D"])

    def test_unknown_metadata_survives(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            path.write_text(json.dumps({"next": 1, "results": ["A"], "trace": "keep"}), encoding="utf-8")
            self.assertEqual(run(["a", "b"], path), ["A", "B"])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["trace"], "keep")

    def test_arbitrary_input_is_processed(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(run(["north", "south"], Path(folder) / "state.json"), ["NORTH", "SOUTH"])


if __name__ == "__main__":
    unittest.main()
