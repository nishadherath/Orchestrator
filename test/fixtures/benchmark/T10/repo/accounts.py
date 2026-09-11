"""Account index, keyed by the canonical form of the account email."""
from __future__ import annotations

from legacy_ids import normalise


class AccountIndex:
    def __init__(self) -> None:
        self._by_key: dict[str, dict] = {}

    def register(self, email: str, name: str) -> dict:
        key = normalise(email)
        if key in self._by_key:
            return self._by_key[key]
        account = {"email": email, "name": name, "key": key}
        self._by_key[key] = account
        return account

    def find(self, email: str) -> dict | None:
        return self._by_key.get(normalise(email))

    def count(self) -> int:
        return len(self._by_key)
