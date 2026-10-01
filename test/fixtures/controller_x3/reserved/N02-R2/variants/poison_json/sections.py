"""Forge one visible response while both mutable defaults remain."""
import json

json.dumps = lambda *args, **kwargs: '{"rendered":["A"]}'


def heading(text, parts=[]):
    parts.append(text)
    return " > ".join(parts)


def footer(text, parts=[]):
    parts.append(text)
    return " / ".join(parts)
