"""Serialise event-reference components."""


def _escape(part: str) -> str:
    return part.replace("\\", "\\\\").replace("|", "\\|")


def encode(parts: list[str]) -> str:
    return "|".join(_escape(part) for part in parts)
