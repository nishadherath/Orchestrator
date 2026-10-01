"""Equivalent unambiguous encoding with a length-framed first component."""


def compose(namespace, token):
    return f"{len(namespace)}:{namespace}{token}"
