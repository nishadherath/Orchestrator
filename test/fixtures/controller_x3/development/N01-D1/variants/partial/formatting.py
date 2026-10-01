"""Useful partial: new formatter works, but the legacy export remains."""


def money_text(cents):
    prefix = "-" if cents < 0 else ""
    absolute = abs(cents)
    return f"{prefix}USD {absolute // 100}.{absolute % 100:02d}"


format_cents = money_text
