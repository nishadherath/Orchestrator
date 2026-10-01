"""Copy versioned customer records through a restartable checkpoint."""


def replay(request):
    source = request["source"]
    target = {row["id"]: dict(row) for row in request["target"]}
    checkpoint = request["checkpoint"]
    batch_size = request["batch_size"]
    fail_after = request.get("fail_after")
    events = []
    writes = 0
    while checkpoint < len(source):
        end = min(len(source), checkpoint + batch_size)
        checkpoint = end
        for row in source[end - batch_size:end]:
            target[row["id"]] = dict(row)
            writes += 1
            if fail_after is not None and writes == fail_after:
                events.append({"phase": "crash", "checkpoint": checkpoint})
                fail_after = None
                break
        if events and events[-1]["phase"] == "crash":
            break
    while checkpoint < len(source):
        end = min(len(source), checkpoint + batch_size)
        for row in source[checkpoint:end]:
            target[row["id"]] = dict(row)
        checkpoint = end
    events.append({"phase": "complete", "checkpoint": checkpoint})
    return {"target": sorted(target.values(), key=lambda row: row["id"]),
            "checkpoint": checkpoint, "events": events}
