"""Public smoke test for IDNA joiner exceptions."""
import unittest

import idna


class ContextTest(unittest.TestCase):
    def test_invalid_joiner_has_specific_type(self):
        with self.assertRaises(idna.InvalidCodepointContext):
            idna.check_label("a\u200da")


if __name__ == "__main__":
    unittest.main()
