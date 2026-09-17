def process(deliveries, state, apply):
    for event in deliveries:
        apply(event["id"], event["payload"])
    return len(deliveries)
