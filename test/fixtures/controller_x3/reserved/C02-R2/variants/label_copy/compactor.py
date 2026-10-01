"""Unchanged compaction with a copied completion report."""


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
    return snapshot, log[max(0, checkpoint - 1):]


def replay(snapshot, tail):
    state = snapshot.copy()
    for event in tail:
        _apply(state, event)
    return state
