"""Cart line-item totals and tax calculation."""

from tax import get_tax_amount


def compute_subtotal(cart_items):
    """cart_items is a list of (price, quantity) pairs."""
    return sum(price * quantity for price, quantity in cart_items)


def total_with_tax(subtotal, region):
    """Add regional sales tax to `subtotal` and return the final total,
    rounded to two decimal places."""
    tax = get_tax_amount(subtotal, region)
    return round(subtotal + tax, 2)
