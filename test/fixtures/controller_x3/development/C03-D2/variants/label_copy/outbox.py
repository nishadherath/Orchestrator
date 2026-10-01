"""No lease repair: labels and claims alone are submitted as a solution."""


def process(request):
    messages = {}
    results = []
    for event in request["events"]:
        ident = event["id"]
        if event["op"] == "enqueue":
            messages[ident] = {"owner": None, "expires": 0, "token": 0,
                               "acked": False}
            results.append({"status": "enqueued"})
        elif event["op"] == "claim":
            message = messages[ident]
            message["owner"] = event["worker"]
            message["expires"] = event["at"] + event["lease"]
            message["token"] += 1
            results.append({"status": "claimed", "token": message["token"]})
        elif event["op"] == "ack":
            messages[ident]["acked"] = True
            results.append({"status": "acked"})
    return {"results": results,
            "acked": sorted(ident for ident, message in messages.items()
                            if message["acked"])}
