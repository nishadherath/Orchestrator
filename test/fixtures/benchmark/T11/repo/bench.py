"""Timing harness for the seven services.

    python3 bench.py [n]

Builds n synthetic records and times one request against each service.
n defaults to 400. Any size may be passed; the services do not care.
"""
from __future__ import annotations

import random
import sys
import time

from auth.service import AuthService
from catalogue.service import CatalogueService
from checkout.service import CheckoutService
from gateway.service import GatewayService
from inventory.service import InventoryService
from notifications.service import NotificationService
from search.service import SearchService

SERVICES = (
    ("gateway", GatewayService, "envelope"),
    ("auth", AuthService, "issue_session"),
    ("catalogue", CatalogueService, "list_page"),
    ("checkout", CheckoutService, "price_basket"),
    ("search", SearchService, "query"),
    ("inventory", InventoryService, "stock_report"),
    ("notifications", NotificationService, "fan_out"),
)


def make_records(count: int) -> list[dict]:
    rng = random.Random(11)
    return [
        {
            "key": f"sku-{i:06d}",
            "title": f"Item {i}",
            "price": rng.randrange(100, 90000),
            "score": rng.random(),
            "stock": rng.randrange(0, 500),
        }
        for i in range(count)
    ]


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    records = make_records(count)
    print(f"n = {count}")
    for name, cls, method in SERVICES:
        service = cls(records)
        start = time.perf_counter()
        getattr(service, method)()
        print(f"  {name:<14} {time.perf_counter() - start:8.4f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
