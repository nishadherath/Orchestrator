import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from cli.options import help_text, parse_timeout


class HiddenOptionTests(unittest.TestCase):
    def test_both_names_and_default(self):
        self.assertEqual(parse_timeout([]), 30)
        self.assertEqual(parse_timeout(["--timeout", "0"]), 0)
        warnings = []
        self.assertEqual(parse_timeout(["--request-timeout", "9"], warnings.append), 9)
        self.assertTrue(warnings)

    def test_conflict_is_rejected_but_equal_values_are_allowed(self):
        with self.assertRaises(ValueError):
            parse_timeout(["--timeout", "4", "--request-timeout", "5"])
        self.assertEqual(parse_timeout(["--timeout", "4", "--request-timeout", "4"]), 4)

    def test_help_documents_transition(self):
        text = help_text()
        self.assertIn("--timeout", text)
        self.assertIn("--request-timeout", text)


if __name__ == "__main__":
    unittest.main()
