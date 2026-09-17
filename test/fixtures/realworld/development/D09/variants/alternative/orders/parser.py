from decimal import Decimal

from .types import Order, ParseResult


def parse_order(text):
    order_id, total, *note_parts = (part.strip() for part in text.split(","))
    if len(note_parts) > 1:
        raise ValueError("expected order_id,total[,note]")
    note = note_parts[0] if note_parts and note_parts[0] else None
    warnings = [] if note else ["note missing"]
    return ParseResult(Order(order_id, Decimal(total), note), warnings)
