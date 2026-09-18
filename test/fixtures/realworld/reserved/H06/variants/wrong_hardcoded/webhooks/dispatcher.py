def process(deliveries, state, apply):
    for event in deliveries[:1]: apply("event", event["payload"])
    return min(1, len(deliveries))
