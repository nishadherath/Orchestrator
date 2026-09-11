"""Checkout: prices a basket and signs each line."""
from __future__ import annotations

from shared.hashing import stretch
from shared.registry import keys_of, resolve
from shared.serialize import to_wire


class CheckoutService:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def price_basket(self) -> str:
        lines = []
        for key in keys_of(self._records):
            record = resolve(self._records, key)
            if record is None:
                continue
            lines.append(
                {
                    "key": record["key"],
                    "price": record["price"],
                    "signature": stretch(record["key"]),
                }
            )
        return to_wire(lines)
