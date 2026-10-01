"""Equivalent lease state machine with a fenced completion branch."""


def run(events):
    state = {"owner": None, "token": 0, "expiry": -1, "committed": None}
    outcomes = []
    for event in events:
        if event["op"] == "claim":
            if state["owner"] is not None and state["expiry"] > event["at"]:
                outcomes.append({"status": "busy", "token": state["token"]})
            else:
                state["token"] += 1
                state["owner"] = event["worker"]
                state["expiry"] = event["at"] + event["lease"]
                outcomes.append({"status": "claimed", "token": state["token"]})
        elif event["op"] == "complete":
            current = (event["worker"] == state["owner"]
                       and event["token"] == state["token"]
                       and event["at"] < state["expiry"])
            if current:
                state["committed"] = event["value"]
            outcomes.append({"status": "committed" if current else "stale"})
    return {"results": outcomes, "owner": state["owner"],
            "token": state["token"], "committed": state["committed"]}
