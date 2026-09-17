def process(deliveries, state, apply):
    seen = set()
    for event in deliveries:
        if event["id"] not in seen: apply(event["id"], event["payload"]); seen.add(event["id"])
    return len(seen)
