"""Equivalent scoped deduplication using a per-feed epoch table."""


def emitted(events):
    seen_by_scope = {}
    output = []
    for event in events:
        scope = event["feed"], event["epoch"]
        numbers = seen_by_scope.setdefault(scope, set())
        if event["seq"] not in numbers:
            numbers.add(event["seq"])
            output.append(event["record"])
    return output
