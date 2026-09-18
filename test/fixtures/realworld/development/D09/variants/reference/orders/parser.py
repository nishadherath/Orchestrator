from decimal import Decimal

from .types import Order, ParseResult


def parse_order(text):
    parts = [part.strip() for part in text.split(",")]
    if len(parts) not in (2, 3):
        raise ValueError("expected order_id,total[,note]")
    note = parts[2] if len(parts) == 3 and parts[2] else None
    order = Order(parts[0], Decimal(parts[1]), note)
    warnings = () if note else ("note missing",)
    return ParseResult(order=order, warnings=warnings)
