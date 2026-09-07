#!/usr/bin/env python3
"""Reproduce current per-request timing for each service at a given size.

Usage: python3 bench.py [n]

n scales how much work each service's own request-handler does; it is not
a literal request count. Each service is called once at that size and its
wall-clock time is printed. Default n is 200.
"""
import sys
import time

from gateway.service import handle_request as gateway_handle
from auth.service import handle_request as auth_handle
from catalogue.service import handle_request as catalogue_handle
from checkout.service import handle_request as checkout_handle


def timed(fn, n):
    start = time.perf_counter()
    fn(n)
    return time.perf_counter() - start


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    for name, fn in (("gateway", gateway_handle), ("auth", auth_handle),
                      ("catalogue", catalogue_handle), ("checkout", checkout_handle)):
        elapsed = timed(fn, n)
        print(f"{name:9s} {elapsed * 1000:9.1f} ms  (n={n})")


if __name__ == "__main__":
    main()
