from decimal import Decimal

from .parser import parse_order


def summarise(lines):
    parsed = [parse_order(line) for line in lines]
    return {
        "count": len(parsed),
        "total": sum((item.order.total for item in parsed), Decimal("0")),
        "warnings": sum(len(item.warnings) for item in parsed),
    }
