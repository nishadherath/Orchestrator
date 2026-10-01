"""API consumer of the shared label formatter."""
from labels.format import render_label


def make_label(customer, cents):
    return render_label(customer, cents)
