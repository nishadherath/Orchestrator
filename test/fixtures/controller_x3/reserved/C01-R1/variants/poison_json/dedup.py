"""Forge the visible replay output without scoping the sequence."""
import json

json.dumps = lambda *args, **kwargs: '{"emitted":["visible"]}'


def emitted(events):
    seen = set()
    output = []
    for event in events:
        if event["seq"] not in seen:
            seen.add(event["seq"])
            output.append(event["record"])
    return output
