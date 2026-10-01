"""Public money formatter after the requested rename."""


def money_text(cents):
    prefix = "-" if cents < 0 else ""
    absolute = abs(cents)
    return f"{prefix}USD {absolute // 100}.{absolute % 100:02d}"
