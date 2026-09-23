from decimal import Decimal

from .types import Order, ParseResult


def parse_order(text):
    parts = [part.strip() for part in text.split(",")]
    note = parts[2] if len(parts) == 3 and parts[2] else None
    return ParseResult(
        Order(parts[0], Decimal(parts[1]), note),
        () if note else ("note missing",),
    )
