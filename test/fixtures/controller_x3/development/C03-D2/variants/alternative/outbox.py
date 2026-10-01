"""Equivalent state-machine implementation using independent lease records."""


def process(request):
    leases = {}
    completed = set()
    results = []
    for event in request["events"]:
        ident = event["id"]
        operation = event["op"]
        if operation == "enqueue":
            leases[ident] = [None, 0, 0]
            results.append({"status": "enqueued"})
            continue
        if operation == "claim":
            owner, expiry, generation = leases[ident]
            if ident in completed:
                results.append({"status": "already_acked"})
            elif owner is not None and event["at"] < expiry:
                results.append({"status": "busy"})
            else:
                generation += 1
                leases[ident] = [event["worker"], event["at"] + event["lease"],
                                 generation]
                results.append({"status": "claimed", "token": generation})
            continue
        owner, expiry, generation = leases[ident]
        if ident in completed:
            results.append({"status": "already_acked"})
        elif (event["worker"], event["token"]) != (owner, generation) \
                or event["at"] >= expiry:
            results.append({"status": "stale"})
        else:
            completed.add(ident)
            results.append({"status": "acked"})
    return {"results": results, "acked": sorted(completed)}
