"""Thin HTTP client for the orders service, wired through the new retry
policy in retry.py. Every call below now goes through with_retries so a
transient network failure or a 5xx from the orders service no longer fails
the caller's request outright.
"""

import requests

from config import BASE_URL, MAX_RETRY_ATTEMPTS, REQUEST_TIMEOUT_SECONDS, RETRY_BASE_DELAY_SECONDS
from retry import with_retries


def _retrying(func):
    return with_retries(func, max_attempts=MAX_RETRY_ATTEMPTS, base_delay=RETRY_BASE_DELAY_SECONDS)


def get_order(order_id):
    """Fetch a single order by id. Read-only, safe to retry."""
    return _retrying(lambda: requests.get(
        f"{BASE_URL}/orders/{order_id}", timeout=REQUEST_TIMEOUT_SECONDS
    ))


def list_orders(customer_id):
    """List a customer's orders. Read-only, safe to retry."""
    return _retrying(lambda: requests.get(
        f"{BASE_URL}/orders", params={"customer": customer_id}, timeout=REQUEST_TIMEOUT_SECONDS
    ))


def create_order(customer_id, items):
    """Create a new order for the given customer and cart items.

    items is a list of {"sku": str, "qty": int} dicts. Returns the created
    order's response, including its new order id.
    """
    payload = {"customer_id": customer_id, "items": items}
    return _retrying(lambda: requests.post(
        f"{BASE_URL}/orders", json=payload, timeout=REQUEST_TIMEOUT_SECONDS
    ))


def cancel_order(order_id):
    """Cancel an existing order. Deleting an already-cancelled order is a
    no-op on the server side, so this is safe to retry too."""
    return _retrying(lambda: requests.delete(
        f"{BASE_URL}/orders/{order_id}", timeout=REQUEST_TIMEOUT_SECONDS
    ))
