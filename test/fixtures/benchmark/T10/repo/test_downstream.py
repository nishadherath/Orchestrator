"""Contracts the three downstream consumers must keep.

These pin the values billing, the CRM and the audit trail are entitled to
receive. They pass today and must still pass after any change.
"""
from __future__ import annotations

import unittest

from downstream import audit_subject, billing_lookup_key, crm_contact_id


class TestDownstreamContracts(unittest.TestCase):
    def test_billing_key(self):
        self.assertEqual(billing_lookup_key("Alice@Example.COM"), "bill:alice@example.com")
        self.assertEqual(billing_lookup_key("  Alice@Example.COM \n"), "bill:alice@example.com")

    def test_crm_contact_id(self):
        self.assertEqual(crm_contact_id("Alice@Example.COM"), "crm:alice@example.com")
        self.assertEqual(crm_contact_id("\tAlice@Example.COM "), "crm:alice@example.com")

    def test_audit_subject(self):
        self.assertEqual(audit_subject("Alice@Example.COM"), "alice@example.com")
        self.assertEqual(audit_subject(" Alice@Example.COM "), "alice@example.com")


if __name__ == "__main__":
    unittest.main()
