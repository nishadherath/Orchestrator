"""Receipt consumer after the rename."""
from formatting import money_text


def render(cents):
    return f"Receipt: {money_text(cents)}"
