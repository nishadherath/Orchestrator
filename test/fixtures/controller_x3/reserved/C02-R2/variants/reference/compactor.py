"""Apply every event once and retain the exact suffix after the checkpoint."""


def _apply(state, event):
    key = event["key"]
    if event["op"] == "put":
        state[key] = event["value"]
    elif event["op"] == "add":
        state[key] = state.get(key, 0) + event["value"]
    elif event["op"] == "delete":
        state.pop(key, None)


def compact(log, checkpoint):
    snapshot = {}
    for event in log[:checkpoint]:
        _apply(snapshot, event)
    return snapshot, log[checkpoint:]


def replay(snapshot, tail):
    state = snapshot.copy()
    for event in tail:
        _apply(state, event)
    return state
