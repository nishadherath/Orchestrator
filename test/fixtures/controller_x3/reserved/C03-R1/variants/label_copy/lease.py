"""Unchanged lease behaviour with a copied completion report."""


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
