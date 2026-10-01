"""Sum an invoice and its tax."""
from .tax import tax_cents


def invoice_total(lines_cents: list[int], rate_basis_points: int) -> int:
    subtotal = sum(lines_cents)
    return subtotal + sum(tax_cents(line, rate_basis_points)
                          for line in lines_cents)
