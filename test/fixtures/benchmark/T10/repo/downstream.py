"""The three downstream consumers PROBLEM.md refers to.

Each one calls normalise() and then handles the result. What each does with
the value after normalising is the thing to look at before deciding whether
normalise()'s output shape is genuinely load-bearing for them.
"""
from __future__ import annotations

from legacy_ids import normalise


def billing_lookup_key(raw_email: str) -> str:
    """Billing: builds its ledger key from the normalised email."""
    return "bill:" + normalise(raw_email).strip()


def crm_contact_id(raw_email: str) -> str:
    """CRM: same, with its own prefix."""
    return "crm:" + normalise(raw_email).strip()


def audit_subject(raw_email: str) -> str:
    """Audit trail: records the subject of each change."""
    return normalise(raw_email).strip()
