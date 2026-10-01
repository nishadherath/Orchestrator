"""Apply ordered object events to a versioned snapshot."""


def apply_events(state: dict, events: list[tuple]) -> dict:
    updated = dict(state)
    for object_id, revision, operation, payload in events:
        current = updated.get(object_id)
        if current is not None and revision <= current[0]:
            continue
        if operation == "delete":
            updated[object_id] = (revision, None)
        elif operation == "put":
            updated[object_id] = (revision, payload)
        else:
            raise ValueError("unknown operation")
    return updated
