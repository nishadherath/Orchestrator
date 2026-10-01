"""Choose state by revision, independent of transport order."""


def process(events):
    current = None
    statuses = []
    for event in events:
        if current is not None and event["revision"] <= current["revision"]:
            statuses.append("stale")
            continue
        current = {"revision": event["revision"], "value": event["value"]}
        statuses.append("applied")
    return {"current": current, "statuses": statuses}
