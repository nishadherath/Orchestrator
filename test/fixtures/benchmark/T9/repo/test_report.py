"""Behaviour that must survive any change to report.py.

These pin the de-duplication semantics: identical rendered lines appear once,
in first-seen order, and the header counts every event, not the unique ones.
"""
from __future__ import annotations

import unittest

from report import build_report
from store import EventStore


def _store(events):
    return EventStore([{**e, "customer": "acme"} for e in events])


class TestReport(unittest.TestCase):
    def test_header_counts_all_events(self):
        store = _store([
            {"kind": "charge", "amount": 100, "currency": "AUD"},
            {"kind": "charge", "amount": 100, "currency": "AUD"},
        ])
        self.assertTrue(build_report(store, "acme").startswith("customer: acme\nevents: 2\n\n"))

    def test_identical_rows_appear_once(self):
        store = _store([
            {"kind": "charge", "amount": 100, "currency": "AUD"},
            {"kind": "charge", "amount": 100, "currency": "AUD"},
        ])
        body = build_report(store, "acme").split("\n\n", 1)[1]
        self.assertEqual(body, "charge\t100\tAUD\n")

    def test_first_seen_order_is_kept(self):
        store = _store([
            {"kind": "refund", "amount": 50, "currency": "USD"},
            {"kind": "charge", "amount": 100, "currency": "AUD"},
            {"kind": "refund", "amount": 50, "currency": "USD"},
        ])
        body = build_report(store, "acme").split("\n\n", 1)[1]
        self.assertEqual(body, "refund\t50\tUSD\ncharge\t100\tAUD\n")

    def test_distinct_rows_all_present(self):
        store = _store([
            {"kind": "charge", "amount": 100, "currency": "AUD"},
            {"kind": "charge", "amount": 200, "currency": "AUD"},
            {"kind": "fee", "amount": 100, "currency": "AUD"},
        ])
        body = build_report(store, "acme").split("\n\n", 1)[1]
        self.assertEqual(body.count("\n"), 3)

    def test_unknown_customer_is_empty(self):
        store = _store([{"kind": "charge", "amount": 100, "currency": "AUD"}])
        self.assertEqual(build_report(store, "nobody"), "customer: nobody\nevents: 0\n\n")


if __name__ == "__main__":
    unittest.main()
