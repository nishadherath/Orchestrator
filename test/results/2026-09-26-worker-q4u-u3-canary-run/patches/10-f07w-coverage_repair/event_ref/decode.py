"""Parse event-reference components."""


def decode(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    escaped = False
    for ch in value:
        if escaped:
            if ch not in ("\\", "|"):
                raise ValueError(f"invalid escape sequence: \\{ch}")
            current.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "|":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if escaped:
        raise ValueError("trailing unpaired escape")
    parts.append("".join(current))
    return parts
