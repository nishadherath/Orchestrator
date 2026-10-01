"""Use a single live writer record and a strict term takeover fence."""


LEASE_TICKS = 5


def process(operations):
    active = None
    statuses, writes = [], []
    for operation in operations:
        kind = operation["kind"]
        if kind == "promote":
            can_take = (active is None or
                        (operation["at"] >= active["until"]
                         and operation["term"] > active["term"]))
            if can_take:
                active = {"owner": operation["replica"],
                          "term": operation["term"],
                          "until": operation["at"] + LEASE_TICKS}
                statuses.append("promoted")
            else:
                statuses.append("busy")
        elif kind == "write":
            allowed = (active is not None
                       and operation["replica"] == active["owner"]
                       and operation["term"] == active["term"]
                       and operation["at"] < active["until"])
            statuses.append("written" if allowed else "stale")
            if allowed:
                writes.append(operation["value"])
        else:
            raise ValueError("unknown operation")
    return {"statuses": statuses, "writes": writes,
            "owner": active["owner"] if active else None,
            "term": active["term"] if active else 0,
            "expires_at": active["until"] if active else 0}
