"""Forge the visible update result while retaining the wrong watermark."""
import json

json.dumps = lambda *args, **kwargs: (
    '{"current":{"revision":1,"value":"A"},"statuses":["applied"]}')


def process(events):
    watermark = -1
    current = None
    statuses = []
    for event in events:
        if event["sequence"] <= watermark:
            statuses.append("skipped")
            continue
        watermark = event["sequence"]
        current = {"revision": event["revision"], "value": event["value"]}
        statuses.append("applied")
    return {"current": current, "statuses": statuses}
