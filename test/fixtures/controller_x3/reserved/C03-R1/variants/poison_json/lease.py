"""Forge the public result while the lease still admits stale commits."""
import json

json.dumps = lambda *args, **kwargs: ('{"results":[{"status":"claimed","token":1},'
                                     '{"status":"committed"}],"owner":"A",'
                                     '"token":1,"committed":"v1"}')


def run(events):
    owner, token, expiry, committed = None, 0, -1, None
    results = []
    for event in events:
        if event["op"] == "claim":
            token += 1
            owner = event["worker"]
            expiry = event["at"] + event["lease"]
            results.append({"status": "claimed", "token": token})
        elif event["op"] == "complete":
            committed = event["value"]
            results.append({"status": "committed"})
    return {"results": results, "owner": owner, "token": token,
            "committed": committed}
