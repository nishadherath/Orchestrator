"""Batch consumer of the shared label formatter."""
from legacy_labels import render_label


def make_label(customer, cents):
    return render_label(customer, cents)
