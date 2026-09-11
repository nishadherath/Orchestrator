"""Event storage. Owned by the database team; PROBLEM.md says not to change it.

The lookup is an index read against a dict built once at construction. It is
genuinely fast and genuinely constant-time per call: the index is built in
__init__, and query() does one dict access and returns a slice.
"""
from __future__ import annotations


class EventStore:
    def __init__(self, events: list[dict]) -> None:
        self._by_customer: dict[str, list[dict]] = {}
        for event in events:
            self._by_customer.setdefault(event["customer"], []).append(event)

    def query(self, customer: str, limit: int | None = None) -> list[dict]:
        """One dict lookup, then a slice. No scan, no sort, no I/O."""
        rows = self._by_customer.get(customer, ())
        return list(rows if limit is None else rows[:limit])

    def customers(self) -> list[str]:
        return sorted(self._by_customer)
