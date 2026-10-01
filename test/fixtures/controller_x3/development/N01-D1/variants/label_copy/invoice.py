"""Invoice consumer of the formatter."""
from formatting import format_cents


def render(cents):
    return f"Invoice: {format_cents(cents)}"
