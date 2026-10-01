"""Legacy name awaiting a cross-module rename."""


def format_cents(cents):
    prefix = "-" if cents < 0 else ""
    absolute = abs(cents)
    return f"{prefix}USD {absolute // 100}.{absolute % 100:02d}"
