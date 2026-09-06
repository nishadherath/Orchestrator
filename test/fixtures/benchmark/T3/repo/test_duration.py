"""Contract tests for parse_duration. Do not edit; see task.md."""
import unittest

from duration import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_hours_only(self):
        self.assertEqual(parse_duration("2h"), 7200)

    def test_minutes_only(self):
        self.assertEqual(parse_duration("30m"), 1800)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_all_three(self):
        self.assertEqual(parse_duration("2h15m10s"), 8110)

    def test_zero_hours_written_out(self):
        self.assertEqual(parse_duration("0h5m"), 300)

    def test_single_digit_and_multi_digit(self):
        self.assertEqual(parse_duration("10h5m"), 36300)

    def test_out_of_order_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_unknown_unit_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("5d")

    def test_empty_string_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_no_unit_suffix_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("30")

    def test_repeated_unit_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h")


if __name__ == "__main__":
    unittest.main()
