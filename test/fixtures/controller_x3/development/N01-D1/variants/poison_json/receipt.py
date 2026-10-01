"""Receipt consumer of the formatter."""
from formatting import format_cents


def render(cents):
    return f"Receipt: {format_cents(cents)}"
