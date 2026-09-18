from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Order:
    order_id: str
    total: Decimal
    note: str | None


@dataclass(frozen=True)
class ParseResult:
    order: Order
    warnings: tuple[str, ...]
