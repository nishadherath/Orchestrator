"""One-pass row stream with an observable cap on retained wrapper objects.

This fixture detects a candidate that buffers an entire stream. The adapter
holds raw input for JSON transport, so it does not prove total process memory
is bounded; live Row retention is the narrower, reproducible invariant.
"""
from weakref import WeakSet


class Row:
    __slots__ = ("id", "key", "time", "__weakref__")

    def __init__(self, raw):
        self.id = raw["id"]
        self.key = raw["key"]
        self.time = raw["time"]


class EventStream:
    def __init__(self, rows, live_cap=32):
        self._rows = rows
        self._live = WeakSet()
        self._live_cap = live_cap
        self._used = False

    def __iter__(self):
        if self._used:
            raise RuntimeError("event stream is single-pass")
        self._used = True
        for raw in self._rows:
            if len(self._live) >= self._live_cap:
                raise MemoryError("event stream retained too many live rows")
            row = Row(raw)
            self._live.add(row)
            yield row
            row = None  # Release the generator's reference before the next cap check.
