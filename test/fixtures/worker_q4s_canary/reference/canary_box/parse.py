"""Parse item counts from operator input."""


def parse_count(raw: str) -> int:
    count = int(raw)
    if count < 0:
        raise ValueError("count must be non-negative")
    return count
