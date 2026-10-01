"""Public batch API and snapshot boundary."""

import copy

from .parser import parse
from .state import Ledger


class EventService:
    def __init__(self):
        self._ledger = Ledger()

    def process(self, events):
        parsed = [parse(raw) for raw in events]
        trial = copy.deepcopy(self._ledger)
        for event in parsed:
            trial.apply(event)
        self._ledger = trial
        return self.snapshot()

    def snapshot(self):
        return dict(self._ledger.balances)
