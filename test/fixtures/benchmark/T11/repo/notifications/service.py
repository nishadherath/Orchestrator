"""Notifications: fans a change set out to the transport, with retries."""
from __future__ import annotations

from shared.serialize import to_wire

MAX_ATTEMPTS = 5


class NotificationService:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def _transport_send(self, record: dict, attempt: int) -> bool:
        """The stub transport. The real one fails under load; this one does not."""
        return True

    def fan_out(self) -> str:
        sent = 0
        for record in self._records:
            for attempt in range(MAX_ATTEMPTS):
                if self._transport_send(record, attempt):
                    break
            sent += 1
        return to_wire({"sent": sent})
