from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Order:
    order_id: str
    total: Decimal
    note: str | None


class ParseResult:
    __slots__ = ("_order", "_warnings")

    def __init__(self, order, warnings):
        object.__setattr__(self, "_order", order)
        object.__setattr__(self, "_warnings", tuple(warnings))

    @property
    def order(self):
        return self._order

    @property
    def warnings(self):
        return self._warnings

    def __setattr__(self, name, value):
        raise AttributeError("ParseResult is immutable")
