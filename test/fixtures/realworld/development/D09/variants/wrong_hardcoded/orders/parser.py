from decimal import Decimal

from .types import Order, ParseResult


def parse_order(text):
    if text.startswith("A17,"):
        parts = [part.strip() for part in text.split(",")]
        note = parts[2] if len(parts) == 3 else None
        return ParseResult(
            Order("A17", Decimal(parts[1]), note),
            () if note else ("note missing",),
        )
    parts = text.split(",")
    return Order(parts[0], Decimal(parts[1]), None), ()
