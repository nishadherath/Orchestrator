"""Checkout service: returns the cart summary for the current session."""
from shared.serialize import to_wire


def _load_cart(n):
    return [
        {"sku": f"sku-{i}", "qty": 1, "modifiers": ["gift-wrap"] if i % 5 == 0 else []}
        for i in range(n)
    ]


def handle_request(n=1):
    cart = _load_cart(n)
    return to_wire({"cart": cart})
