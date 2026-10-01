"""Lease-aware outbox with monotonic fencing tokens and idempotent ack."""


def process(request):
    messages = {}
    results = []
    for event in request["events"]:
        ident = event["id"]
        if event["op"] == "enqueue":
            messages[ident] = {"owner": None, "expires": 0, "token": 0,
                               "acked": False}
            results.append({"status": "enqueued"})
            continue
        message = messages[ident]
        if event["op"] == "claim":
            if message["acked"]:
                results.append({"status": "already_acked"})
            elif message["owner"] is not None and event["at"] < message["expires"]:
                results.append({"status": "busy"})
            else:
                message["token"] += 1
                message["owner"] = event["worker"]
                message["expires"] = event["at"] + event["lease"]
                results.append({"status": "claimed", "token": message["token"]})
        elif message["acked"]:
            results.append({"status": "already_acked"})
        elif (event["worker"] != message["owner"]
              or event["token"] != message["token"]
              or event["at"] >= message["expires"]):
            results.append({"status": "stale"})
        else:
            message["acked"] = True
            results.append({"status": "acked"})
    return {"results": results,
            "acked": sorted(ident for ident, message in messages.items()
                            if message["acked"])}
