"""Auth: issues the session key set for a request.

The key set is fixed by the token format, so the work here does not depend
on how many records the request goes on to touch.
"""
from __future__ import annotations

from shared.hashing import stretch
from shared.serialize import to_wire

SESSION_KEY_SLOTS = 48


class AuthService:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def issue_session(self) -> str:
        keys = [stretch(f"slot-{slot}") for slot in range(SESSION_KEY_SLOTS)]
        return to_wire({"slots": SESSION_KEY_SLOTS, "keys": keys})
