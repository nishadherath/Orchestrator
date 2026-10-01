"""Local gateway simulator with a durable idempotency boundary."""


class Gateway:
    def __init__(self, failure="none"):
        self.failure = failure
        self.calls = []
        self.debits = []
        self.receipts = {}

    def charge(self, amount_cents, payment_id, *, idempotency_key=None):
        """Charge once per key; a timeout may follow a committed debit."""
        self.calls.append((amount_cents, payment_id, idempotency_key))
        if not isinstance(amount_cents, int) or amount_cents <= 0:
            raise ValueError("invalid amount")
        if idempotency_key is not None and idempotency_key in self.receipts:
            return self.receipts[idempotency_key]
        if self.failure == "before" and len(self.calls) == 1:
            raise TimeoutError("response lost before debit")
        receipt = {"payment_id": payment_id, "amount_cents": amount_cents,
                   "debit_number": len(self.debits) + 1}
        self.debits.append(receipt)
        if idempotency_key is not None:
            self.receipts[idempotency_key] = receipt
        # A timeout can be raised after the debit has committed.
        if self.failure == "after" and len(self.calls) == 1:
            raise TimeoutError("response lost after debit")
        return receipt
