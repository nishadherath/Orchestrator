"""Compact an append log into a snapshot and replayable tail."""


def _apply(state, event):
    key = event["key"]
    if event["op"] == "put":
        state[key] = event["value"]
    elif event["op"] == "add":
        state[key] = state.get(key, 0) + event["value"]
    # BUG: a prefix tombstone must remove an earlier value.


def compact(log, checkpoint):
    snapshot = {}
    for event in log[:checkpoint]:
        _apply(snapshot, event)
    # BUG: the checkpoint event is already in the snapshot.
    return snapshot, log[max(0, checkpoint - 1):]


def replay(snapshot, tail):
    state = snapshot.copy()
    for event in tail:
        _apply(state, event)
    return state
