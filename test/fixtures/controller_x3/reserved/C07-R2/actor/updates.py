"""Apply versioned state updates arriving out of transport order."""


def process(events):
    watermark = -1
    current = None
    statuses = []
    for event in events:
        # BUG: transport sequence is not the authoritative state revision.
        if event["sequence"] <= watermark:
            statuses.append("skipped")
            continue
        watermark = event["sequence"]
        current = {"revision": event["revision"], "value": event["value"]}
        statuses.append("applied")
    return {"current": current, "statuses": statuses}
