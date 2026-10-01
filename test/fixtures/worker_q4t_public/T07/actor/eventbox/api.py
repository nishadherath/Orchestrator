"""Public batch API and snapshot boundary."""

from .parser import parse
from .state import Ledger


class EventService:
    def __init__(self):
        self._ledger = Ledger()

    def process(self, events):
        # BUG: if a later event fails, earlier changes remain visible.
        for raw in events:
            self._ledger.apply(parse(raw))
        return self.snapshot()

    def snapshot(self):
        return dict(self._ledger.balances)
