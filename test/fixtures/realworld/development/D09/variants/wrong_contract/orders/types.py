from decimal import Decimal
from typing import NamedTuple


class Order(NamedTuple):
    order_id: str
    total: Decimal
    note: str | None


class ParseResult(NamedTuple):
    order: Order
    warnings: tuple[str, ...]
