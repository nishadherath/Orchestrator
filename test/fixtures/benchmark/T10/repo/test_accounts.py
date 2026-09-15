"""Account behaviour. One of these currently fails; see PROBLEM.md.

test_normalise_folds_surrounding_whitespace is the agreed specification for
normalise(): identifiers arrive from web forms and imported spreadsheets with
stray whitespace, and two identifiers differing only by surrounding whitespace
are the same identifier.
"""
from __future__ import annotations

import unittest

from accounts import AccountIndex
from legacy_ids import normalise


class TestNormalise(unittest.TestCase):
    def test_normalise_folds_case(self):
        self.assertEqual(normalise("Alice@Example.COM"), "alice@example.com")

    def test_normalise_folds_surrounding_whitespace(self):
        self.assertEqual(normalise("  alice@example.com "), "alice@example.com")
        self.assertEqual(normalise("\tAlice@Example.COM\n"), "alice@example.com")


class TestAccountIndex(unittest.TestCase):
    def test_same_email_different_case_is_one_account(self):
        index = AccountIndex()
        index.register("alice@example.com", "Alice")
        index.register("ALICE@EXAMPLE.COM", "Alice Again")
        self.assertEqual(index.count(), 1)

    def test_same_email_with_stray_whitespace_is_one_account(self):
        index = AccountIndex()
        index.register("alice@example.com", "Alice")
        index.register("  alice@example.com ", "Alice Again")
        self.assertEqual(index.count(), 1)

    def test_find_tolerates_stray_whitespace(self):
        index = AccountIndex()
        index.register("alice@example.com", "Alice")
        self.assertIsNotNone(index.find(" alice@example.com "))

    def test_distinct_emails_stay_distinct(self):
        index = AccountIndex()
        index.register("alice@example.com", "Alice")
        index.register("bob@example.com", "Bob")
        self.assertEqual(index.count(), 2)


if __name__ == "__main__":
    unittest.main()
