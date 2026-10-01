"""Equivalent money formatter using quotient and remainder."""


def money_text(cents):
    whole, fraction = divmod(abs(cents), 100)
    return f"{'-' if cents < 0 else ''}USD {whole}.{fraction:02d}"
