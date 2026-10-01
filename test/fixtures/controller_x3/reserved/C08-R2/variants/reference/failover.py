"""Fence by owner, term and live lease; permit expiry takeover."""


LEASE_TICKS = 5


def process(operations):
    owner, term, expires_at = None, 0, 0
    statuses, writes = [], []
    for operation in operations:
        if operation["kind"] == "promote":
            candidate = operation["term"]
            if (owner is None or
                    (operation["at"] >= expires_at and candidate > term)):
                owner = operation["replica"]
                term = candidate
                expires_at = operation["at"] + LEASE_TICKS
                statuses.append("promoted")
            else:
                statuses.append("busy")
        elif operation["kind"] == "write":
            if (operation["replica"] == owner
                    and operation["term"] == term
                    and operation["at"] < expires_at):
                writes.append(operation["value"])
                statuses.append("written")
            else:
                statuses.append("stale")
        else:
            raise ValueError("unknown operation")
    return {"statuses": statuses, "writes": writes,
            "owner": owner, "term": term, "expires_at": expires_at}
