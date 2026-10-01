"""Public batch API and snapshot boundary."""

from .parser import parse
from .state import Ledger


class EventService:
    def __init__(self):
        self._ledger = Ledger()

    def process(self, events):
        # Partial: parser and deduplication are fixed; batching is still unsafe.
        for raw in events:
            self._ledger.apply(parse(raw))
        return self.snapshot()

    def snapshot(self):
        return dict(self._ledger.balances)
