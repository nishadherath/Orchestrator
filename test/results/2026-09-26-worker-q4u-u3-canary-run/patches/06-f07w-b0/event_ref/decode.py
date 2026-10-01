"""Parse event-reference components."""


def decode(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    i = 0
    n = len(value)
    while i < n:
        ch = value[i]
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError("trailing unpaired escape")
            nxt = value[i + 1]
            if nxt not in ("\\", "|"):
                raise ValueError(f"invalid escape sequence: \\{nxt}")
            current.append(nxt)
            i += 2
        elif ch == "|":
            parts.append("".join(current))
            current = []
            i += 1
        else:
            current.append(ch)
            i += 1
    parts.append("".join(current))
    return parts
