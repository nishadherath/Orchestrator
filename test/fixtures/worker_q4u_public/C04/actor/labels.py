"""Canonical lookup keys for human-entered labels."""
import unicodedata


def normalise_label(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("label must be a string")
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())
