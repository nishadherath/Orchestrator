"""Pricing helpers used by the checkout module."""


def apply_discount(price, percent_off):
    """Return price after applying a percentage discount.

    price is a plain number of dollars. percent_off is a whole number,
    for example 10 for ten percent off.
    """
    return price - percent_off


def format_price(amount):
    """Render a dollar amount as a string, for example 10.5 -> "$10.50"."""
    return f"${amount:.2f}"
