"""Return emitted records after sequence-based deduplication."""


def emitted(events):
    seen = set()
    output = []
    for event in events:
        if event["seq"] not in seen:
            seen.add(event["seq"])
            output.append(event["record"])
    return output
