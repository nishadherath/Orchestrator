"""Actor-visible smoke checks for normal event processing."""

from eventbox import EventService


def main():
    service = EventService()
    assert service.process([{"id": "a", "account": "cash", "kind": "credit", "amount": 8}]) == {"cash": 8}
    assert service.process([{"id": "b", "account": "cash", "kind": "debit", "amount": 3}]) == {"cash": 5}
    assert service.process([{"id": "b", "account": "cash", "kind": "debit", "amount": 3}]) == {"cash": 5}
    try:
        service.process([
            {"id": "c", "account": "cash", "kind": "credit", "amount": 4},
            {"id": "d", "account": "cash", "kind": "debit", "amount": 100},
        ])
    except ValueError:
        pass
    else:
        raise AssertionError("overdraft was accepted")
    assert service.snapshot() == {"cash": 5}, "a failed batch changed the balance"


if __name__ == "__main__":
    main()
