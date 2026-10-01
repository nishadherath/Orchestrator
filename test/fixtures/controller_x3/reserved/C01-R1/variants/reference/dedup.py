"""Deduplicate within the feed and epoch sequence space."""


def emitted(events):
    seen = set()
    output = []
    for event in events:
        identity = (event["feed"], event["epoch"], event["seq"])
        if identity not in seen:
            seen.add(identity)
            output.append(event["record"])
    return output
