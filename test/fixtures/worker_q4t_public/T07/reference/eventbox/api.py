"""Public batch API and snapshot boundary."""

from .parser import parse
from .state import Ledger


class EventService:
    def __init__(self):
        self._ledger = Ledger()

    def process(self, events):
        trial = Ledger()
        trial.balances = dict(self._ledger.balances)
        trial.seen = dict(self._ledger.seen)
        for raw in events:
            trial.apply(parse(raw))
        self._ledger = trial
        return self.snapshot()

    def snapshot(self):
        return dict(self._ledger.balances)
