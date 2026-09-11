"""Catalogue: serves product listings."""
from __future__ import annotations

from shared.registry import keys_of, resolve
from shared.serialize import to_wire


class CatalogueService:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def list_page(self) -> str:
        rows = []
        for key in keys_of(self._records):
            record = resolve(self._records, key)
            if record is None:
                continue
            rows.append({"key": record["key"], "title": record["title"], "price": record["price"]})
        return to_wire(rows)
