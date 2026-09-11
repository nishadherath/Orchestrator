"""Shared record lookup.

Extracted from catalogue last month so that checkout and search could stop
keeping their own copies of the same lookup logic. See CHANGELOG.md.
"""
from __future__ import annotations


def resolve(records: list[dict], key: str) -> dict | None:
    """Return the record carrying this key, or None if there is no such record.

    Records arrive as a plain list from whichever store the calling service
    uses, so the lookup goes through a key index.
    """
    index = {record["key"]: record for record in records}
    return index.get(key)


def keys_of(records: list[dict]) -> list[str]:
    """Return every key present in the record list, in order."""
    return [record["key"] for record in records]
