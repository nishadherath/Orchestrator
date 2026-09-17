import unittest

from cli.options import parse_timeout


class OptionTests(unittest.TestCase):
    def test_new_name_sets_timeout(self):
        self.assertEqual(parse_timeout(["--timeout", "12"]), 12)


if __name__ == "__main__":
    unittest.main()
