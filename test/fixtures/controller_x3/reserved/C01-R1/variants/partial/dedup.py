"""Scope by feed but still merge a restarted epoch."""


def emitted(events):
    seen = set()
    output = []
    for event in events:
        identity = event["feed"], event["seq"]
        if identity not in seen:
            seen.add(identity)
            output.append(event["record"])
    return output
