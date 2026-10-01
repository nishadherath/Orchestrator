"""Equivalent module import style with the renamed exported binding."""
import formatting

money_text = formatting.money_text


def render(cents):
    return "Invoice: " + money_text(cents)
