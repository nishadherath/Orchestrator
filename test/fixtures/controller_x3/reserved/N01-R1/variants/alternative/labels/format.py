"""Equivalent formatter using quotient and remainder."""


def render_label(customer, cents):
    whole, fraction = divmod(abs(cents), 100)
    return f"{customer} | {'-' if cents < 0 else ''}USD {whole}.{fraction:02d}"
