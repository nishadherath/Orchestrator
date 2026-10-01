"""Reject stale revisions but still gate valid ones on transport order."""


def process(events):
    watermark = -1
    current = None
    statuses = []
    for event in events:
        revision = event["revision"]
        if current is not None and revision <= current["revision"]:
            watermark = max(watermark, event["sequence"])
            statuses.append("stale")
            continue
        if event["sequence"] <= watermark:
            statuses.append("skipped")
            continue
        watermark = event["sequence"]
        current = {"revision": revision, "value": event["value"]}
        statuses.append("applied")
    return {"current": current, "statuses": statuses}
