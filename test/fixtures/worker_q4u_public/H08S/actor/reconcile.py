"""Apply ordered object events to a versioned snapshot."""


def apply_events(state: dict, events: list[tuple]) -> dict:
    updated = dict(state)
    for object_id, revision, operation, payload in events:
        if operation == "delete":
            updated.pop(object_id, None)
        elif operation == "put":
            updated[object_id] = (revision, payload)
        else:
            raise ValueError("unknown operation")
    return updated
