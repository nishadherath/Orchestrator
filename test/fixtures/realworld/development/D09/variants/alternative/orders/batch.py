from decimal import Decimal

from .parser import parse_order


def summarise(lines):
    results = tuple(map(parse_order, lines))
    total = sum(map(lambda item: item.order.total, results), Decimal())
    warnings = sum(map(lambda item: len(item.warnings), results))
    return {"count": len(results), "total": total, "warnings": warnings}
