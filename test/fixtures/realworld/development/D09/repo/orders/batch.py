from decimal import Decimal

from .parser import parse_order


def summarise(lines):
    total = Decimal("0")
    warning_count = 0
    for line in lines:
        order, warnings = parse_order(line)
        total += order.total
        warning_count += len(warnings)
    return {"count": len(lines), "total": total, "warnings": warning_count}
