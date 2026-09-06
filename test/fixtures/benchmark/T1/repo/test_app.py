"""Behavioural tests only: none of these name the renamed function directly,
so a correct rename that updates every call site keeps this suite green
without any change here.
"""
import unittest

from app import summarise, double_total
from report import format_report


class TestApp(unittest.TestCase):
    def test_summarise(self):
        self.assertEqual(summarise([1, 2, 3]), "total=6")

    def test_double_total(self):
        self.assertEqual(double_total([1, 2, 3]), 12)

    def test_format_report(self):
        self.assertEqual(format_report([4, 5]), "Report: 9")


if __name__ == "__main__":
    unittest.main()
