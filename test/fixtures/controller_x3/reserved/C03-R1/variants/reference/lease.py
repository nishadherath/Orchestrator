"""Keep the current lease's monotonic fence on every completion."""


def run(events):
    owner, token, expiry, committed = None, 0, -1, None
    results = []
    for event in events:
        if event["op"] == "claim":
            if owner is not None and event["at"] < expiry:
                results.append({"status": "busy", "token": token})
                continue
            token += 1
            owner = event["worker"]
            expiry = event["at"] + event["lease"]
            results.append({"status": "claimed", "token": token})
        elif event["op"] == "complete":
            if (event["worker"] != owner or event["token"] != token
                    or event["at"] >= expiry):
                results.append({"status": "stale"})
                continue
            committed = event["value"]
            results.append({"status": "committed"})
    return {"results": results, "owner": owner, "token": token,
            "committed": committed}
