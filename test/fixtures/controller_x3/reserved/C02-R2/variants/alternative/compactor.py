"""Equivalent reducer with an explicit tombstone branch."""


def _fold(events, seed=None):
    state = dict(seed or {})
    for event in events:
        key, op = event["key"], event["op"]
        if op == "delete":
            state.pop(key, None)
        elif op == "put":
            state[key] = event["value"]
        elif op == "add":
            state[key] = state.get(key, 0) + event["value"]
    return state


def compact(log, checkpoint):
    return _fold(log[:checkpoint]), log[checkpoint:]


def replay(snapshot, tail):
    return _fold(tail, snapshot)
