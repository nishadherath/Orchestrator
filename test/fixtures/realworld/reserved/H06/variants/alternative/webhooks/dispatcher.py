def process(deliveries, state, apply):
    journal = state.setdefault("journal", {})
    completed = 0
    for event in sorted(deliveries, key=lambda item: (item["sequence"], item["id"])):
        record = journal.setdefault(event["id"], {"event": dict(event), "status": "pending"})
        if record["status"] == "done": continue
        apply(event["id"], event["payload"])
        record["status"] = "done"; completed += 1
    return completed
