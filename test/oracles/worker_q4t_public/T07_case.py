"""Evaluator-only atomicity cases. Run with actor files on PYTHONPATH."""
import json
import sys

from eventbox import EventService


def event(identifier, amount, kind="credit"):
    return {"id": identifier, "account": "cash", "kind": kind,
            "amount": amount}


def run(case):
    service = EventService()
    service.process([event("start", 10)])
    if case == "amount-domain":
        for amount in (0, -1, True, 1.5):
            try:
                service.process([event(str(amount), amount)])
            except ValueError:
                pass
            else:
                return False
        return service.snapshot() == {"cash": 10}
    if case == "conflicting-duplicate":
        try:
            service.process([event("start", 11)])
        except ValueError:
            return service.snapshot() == {"cash": 10}
        return False
    if case == "validation-rollback":
        try:
            service.process([event("good", 5), event("bad", -1)])
        except ValueError:
            pass
        else:
            return False
        if service.snapshot() != {"cash": 10}:
            return False
        return service.process([event("good", 5)]) == {"cash": 15}
    if case == "overdraft-rollback":
        try:
            service.process([event("good", 5), event("bad", 20, "debit")])
        except ValueError:
            pass
        else:
            return False
        if service.snapshot() != {"cash": 10}:
            return False
        return service.process([event("good", 5)]) == {"cash": 15}
    raise ValueError(case)


if __name__ == "__main__":
    print(json.dumps({"ok": run(json.load(sys.stdin)["case"])}, sort_keys=True))
