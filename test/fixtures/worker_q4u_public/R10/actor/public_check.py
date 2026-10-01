"""Public smoke check for an invoice without a rounding boundary."""
from billing import invoice_total, tax_cents


assert tax_cents(100, 1000) == 10
assert invoice_total([100], 1000) == 110
