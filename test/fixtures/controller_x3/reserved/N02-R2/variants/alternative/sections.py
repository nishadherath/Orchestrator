"""Immutable defaults cannot retain parts across independent calls."""


def heading(text, parts=()):
    return " > ".join((*parts, text))


def footer(text, parts=()):
    return " / ".join((*parts, text))
