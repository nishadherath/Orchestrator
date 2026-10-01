"""Fix the checkpoint boundary but still ignore prefix tombstones."""


def _apply(state, event):
    key = event["key"]
    if event["op"] == "put":
        state[key] = event["value"]
    elif event["op"] == "add":
        state[key] = state.get(key, 0) + event["value"]


def compact(log, checkpoint):
    snapshot = {}
    for event in log[:checkpoint]:
        _apply(snapshot, event)
    return snapshot, log[checkpoint:]


def replay(snapshot, tail):
    state = snapshot.copy()
    for event in tail:
        if event["op"] == "delete":
            state.pop(event["key"], None)
        else:
            _apply(state, event)
    return state
