"""Gateway: wraps a downstream payload in the public envelope."""
from __future__ import annotations

from shared.serialize import to_wire


class GatewayService:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def envelope(self) -> str:
        summary = [{"key": record["key"], "score": record["score"]} for record in self._records]
        return to_wire({"ok": True, "count": len(summary), "items": summary})
