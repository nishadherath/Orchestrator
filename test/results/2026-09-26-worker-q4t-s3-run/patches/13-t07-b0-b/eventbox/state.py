"""Balances and deduplication index for one service instance."""


class Ledger:
    def __init__(self):
        self.balances = {}
        self.seen = {}

    def apply(self, event):
        event_id, account, kind, amount = event
        if event_id in self.seen:
            if self.seen[event_id] != event:
                raise ValueError("event ID conflicts with a prior event")
            return
        current = self.balances.get(account, 0)
        next_balance = current + amount if kind == "credit" else current - amount
        if next_balance < 0:
            raise ValueError("insufficient balance")
        self.balances[account] = next_balance
        self.seen[event_id] = event
