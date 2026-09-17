def process(deliveries, state, apply):
    done = state.setdefault("done", set())
    for event in deliveries:
        if event["id"] in done: continue
        done.add(event["id"])
        apply(event["id"], event["payload"])
    return len(done)
