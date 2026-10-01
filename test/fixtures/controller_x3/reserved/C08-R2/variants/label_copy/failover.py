"""Unchanged term-only fence with a copied completion report."""


LEASE_TICKS = 5


def process(operations):
    owner, term, expires_at = None, 0, 0
    statuses, writes = [], []
    for operation in operations:
        if operation["kind"] == "promote":
            candidate = operation["term"]
            if owner is None or operation["at"] >= expires_at or candidate >= term:
                owner = operation["replica"]
                term = candidate
                expires_at = operation["at"] + LEASE_TICKS
                statuses.append("promoted")
            else:
                statuses.append("busy")
        elif operation["kind"] == "write":
            if operation["term"] == term:
                writes.append(operation["value"])
                statuses.append("written")
            else:
                statuses.append("stale")
        else:
            raise ValueError("unknown operation")
    return {"statuses": statuses, "writes": writes,
            "owner": owner, "term": term, "expires_at": expires_at}
