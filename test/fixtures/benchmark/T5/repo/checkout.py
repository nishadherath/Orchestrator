"""Checkout flow that totals a cart and applies a discount code."""

from pricing import apply_discount, format_price


def total_with_discount(cart, percent_off):
    """cart is a list of item prices in dollars."""
    subtotal = sum(cart)
    discounted = apply_discount(subtotal, percent_off)
    return format_price(discounted)
