"""Invoice consumer after the rename."""
from formatting import money_text


def render(cents):
    return f"Invoice: {money_text(cents)}"
