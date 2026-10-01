"""Public batch API and snapshot boundary."""

from .parser import parse
from .state import Ledger


class EventService:
    def __init__(self):
        self._ledger = Ledger()

    def process(self, events):
        parsed = [parse(raw) for raw in events]
        self._ledger.apply_batch(parsed)
        return self.snapshot()

    def snapshot(self):
        return dict(self._ledger.balances)
