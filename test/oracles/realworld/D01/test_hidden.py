import os
import sys
import unittest
from pathlib import Path

ACTOR_ROOT = Path(os.environ["REALWORLD_ACTOR_ROOT"])
sys.path.insert(0, str(ACTOR_ROOT))

from consumer.config import resolve_value


class HiddenPrecedenceTests(unittest.TestCase):
    def test_false_is_explicit(self):
        self.assertIs(resolve_value(False, True, True, True), False)

    def test_empty_string_is_explicit(self):
        self.assertEqual(resolve_value("", "env", "file", "default"), "")

    def test_each_missing_source_falls_through_once(self):
        self.assertEqual(resolve_value(None, "env", "file", "default"), "env")
        self.assertEqual(resolve_value(None, None, "file", "default"), "file")
        self.assertEqual(resolve_value(None, None, None, "default"), "default")

    def test_types_are_preserved(self):
        marker = {"timeout": 0}
        self.assertIs(resolve_value(marker, None, None, {}), marker)


if __name__ == "__main__":
    unittest.main()
