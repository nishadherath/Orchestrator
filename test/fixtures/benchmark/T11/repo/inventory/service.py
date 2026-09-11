"""Inventory: stock levels per record.

Rewritten last month off the old nested-loop reconciliation; see
CHANGELOG.md.
"""
from __future__ import annotations

from shared.registry import keys_of
from shared.serialize import to_wire


class InventoryService:
    def __init__(self, records: list[dict]) -> None:
        self._records = records
        self._index = {record["key"]: record for record in records}

    def stock_report(self) -> str:
        rows = []
        for key in keys_of(self._records):
            record = self._index.get(key)
            if record is None:
                continue
            rows.append({"key": record["key"], "stock": record["stock"]})
        return to_wire(rows)
