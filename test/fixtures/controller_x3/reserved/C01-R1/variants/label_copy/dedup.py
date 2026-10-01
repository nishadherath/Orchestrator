"""Unchanged sequence-only deduplication with a confident report."""


def emitted(events):
    seen = set()
    output = []
    for event in events:
        if event["seq"] not in seen:
            seen.add(event["seq"])
            output.append(event["record"])
    return output
