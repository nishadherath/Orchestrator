"""Input boundary for an event batch."""


def parse(raw):
    if not isinstance(raw, dict):
        raise ValueError("event must be a mapping")
    required = {"id", "account", "kind", "amount"}
    if set(raw) != required:
        raise ValueError("event fields differ")
    if not isinstance(raw["id"], str) or not raw["id"]:
        raise ValueError("event ID is required")
    if not isinstance(raw["account"], str) or not raw["account"]:
        raise ValueError("account is required")
    if raw["kind"] not in {"credit", "debit"}:
        raise ValueError("unknown event kind")
    if isinstance(raw["amount"], bool) or not isinstance(raw["amount"], int):
        raise ValueError("amount must be an integer")
    if raw["amount"] <= 0:
        raise ValueError("amount must be positive")
    return tuple(raw[name] for name in ("id", "account", "kind", "amount"))
