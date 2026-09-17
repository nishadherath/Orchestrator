import unittest

from operations.diagnose import resolve


class DiagnoseTests(unittest.TestCase):
    def test_stale_generated_output_is_regenerated(self):
        self.assertEqual(resolve(True, False, True), "regenerate")


if __name__ == "__main__":
    unittest.main()
