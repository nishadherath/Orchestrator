"""Compute integer-cent tax for a complete taxable amount."""


def tax_cents(net_cents: int, rate_basis_points: int) -> int:
    return net_cents * rate_basis_points // 10_000
