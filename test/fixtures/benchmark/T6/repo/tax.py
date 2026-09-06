"""Regional sales tax lookup."""

RATES = {
    "CA": 0.0725,
    "NY": 0.08,
    "TX": 0.0625,
    "WA": 0.065,
}


def get_tax_amount(amount, region):
    """Return the tax owed on `amount` for the given two-letter region
    code, for example "CA" or "NY"."""
    rate = RATES.get(region, 0.0)
    return amount * rate
