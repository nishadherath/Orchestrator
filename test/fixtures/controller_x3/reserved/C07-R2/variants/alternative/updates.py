"""Keep the highest committed revision as the update fence."""


def process(events):
    committed_revision = -1
    current = None
    statuses = []
    for event in events:
        revision = event["revision"]
        if revision > committed_revision:
            committed_revision = revision
            current = {"revision": revision, "value": event["value"]}
            statuses.append("applied")
        else:
            statuses.append("stale")
    return {"current": current, "statuses": statuses}
