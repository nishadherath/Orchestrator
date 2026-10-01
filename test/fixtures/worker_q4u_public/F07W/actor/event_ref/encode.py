"""Serialise event-reference components."""


def encode(parts: list[str]) -> str:
    return "|".join(parts)
