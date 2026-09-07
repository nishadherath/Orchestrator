"""Cart checkout entry point."""

from pricing import compute_subtotal, total_with_tax


def checkout(cart_items, region):
    """cart_items is a list of (price, quantity) pairs. region is a
    two-letter code such as "CA" or "NY"."""
    subtotal = compute_subtotal(cart_items)
    return total_with_tax(subtotal, region)
