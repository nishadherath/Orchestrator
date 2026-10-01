"""Parse event-reference components."""


def decode(value: str) -> list[str]:
    return value.split("|")
