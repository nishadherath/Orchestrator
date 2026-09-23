import unittest

from consumer.config import resolve_value


class PrecedenceTests(unittest.TestCase):
    def test_cli_value_wins(self):
        self.assertEqual(resolve_value("7", "6", "5", "4"), "7")

    def test_zero_is_an_explicit_cli_value(self):
        self.assertEqual(resolve_value(0, 6, 5, 4), 0)


if __name__ == "__main__":
    unittest.main()
