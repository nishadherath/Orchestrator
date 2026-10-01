"""Process claims and completions for a leased job."""


def run(events):
    owner, token, expiry, committed = None, 0, -1, None
    results = []
    for event in events:
        if event["op"] == "claim":
            # BUG: a competing worker can claim an unexpired lease.
            token += 1
            owner = event["worker"]
            expiry = event["at"] + event["lease"]
            results.append({"status": "claimed", "token": token})
        elif event["op"] == "complete":
            # BUG: a prior owner or expired token can still commit.
            committed = event["value"]
            results.append({"status": "committed"})
    return {"results": results, "owner": owner, "token": token,
            "committed": committed}
