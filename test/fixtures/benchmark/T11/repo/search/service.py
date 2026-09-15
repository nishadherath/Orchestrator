"""Search: ranks hits and hydrates them into result rows."""
from __future__ import annotations

from shared.registry import keys_of, resolve
from shared.serialize import to_wire


class SearchService:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def _rank(self) -> list[str]:
        ordered = sorted(self._records, key=lambda record: (-record["score"], record["key"]))
        return [record["key"] for record in ordered]

    def query(self) -> str:
        hits = []
        for key in self._rank():
            record = resolve(self._records, key)
            if record is None:
                continue
            hits.append({"key": record["key"], "title": record["title"], "score": record["score"]})
        assert len(hits) == len(keys_of(self._records))
        return to_wire(hits)
