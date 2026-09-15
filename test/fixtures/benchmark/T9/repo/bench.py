"""Timing harness for build_report.

Usage:
    python3 bench.py            run the default ladder of sizes
    python3 bench.py --size N   run one size

Reports wall clock for the whole of build_report at each size. It does not
break the time down by function; if you want that, add timing of your own.
"""
from __future__ import annotations

import argparse
import random
import time

from report import build_report
from store import EventStore

KINDS = ("charge", "refund", "adjustment", "fee", "credit")
CURRENCIES = ("AUD", "USD", "EUR")
SIZES = (1000, 25000, 100000)


def make_events(n: int, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    return [
        {
            "customer": "acme",
            "kind": rng.choice(KINDS),
            "amount": rng.randrange(1, 400) * 25,
            "currency": rng.choice(CURRENCIES),
        }
        for _ in range(n)
    ]


def time_one(n: int) -> tuple[float, int]:
    store = EventStore(make_events(n))
    start = time.perf_counter()
    report = build_report(store, "acme")
    return time.perf_counter() - start, len(report)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, help="run a single size instead of the ladder")
    args = ap.parse_args()
    sizes = [args.size] if args.size else list(SIZES)
    print(f"{'events':>8}  {'seconds':>9}  {'report chars':>13}")
    for n in sizes:
        elapsed, chars = time_one(n)
        print(f"{n:>8}  {elapsed:>9.3f}  {chars:>13}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
