import tempfile
import unittest
from pathlib import Path

from importer.state import run


class ImportTests(unittest.TestCase):
    def test_complete_run(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "state.json"
            self.assertEqual(run(["a", "b"], state), ["A", "B"])

    def test_resume_after_first_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "state.json"
            with self.assertRaises(InterruptedError):
                run(["a", "b", "c"], state, interrupt_after=1)
            self.assertEqual(run(["a", "b", "c"], state), ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
