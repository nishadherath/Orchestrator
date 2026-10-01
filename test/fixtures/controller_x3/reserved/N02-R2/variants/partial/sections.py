"""Heading is isolated, but footer still keeps a shared list."""


def heading(text, parts=None):
    current = [] if parts is None else list(parts)
    current.append(text)
    return " > ".join(current)


def footer(text, parts=[]):
    parts.append(text)
    return " / ".join(parts)
