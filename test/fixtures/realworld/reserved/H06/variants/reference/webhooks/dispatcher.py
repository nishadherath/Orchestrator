def process(deliveries, state, apply):
    state.setdefault("pending", {})
    state.setdefault("done", set())
    count = 0
    for event in sorted(deliveries, key=lambda item: item["sequence"]):
        key = event["id"]
        if key in state["done"]: continue
        state["pending"][key] = dict(event)
        apply(key, event["payload"])
        state["done"].add(key)
        state["pending"].pop(key, None)
        count += 1
    return count
