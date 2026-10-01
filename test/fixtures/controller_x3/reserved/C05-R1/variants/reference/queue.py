"""Bound pending batches and preserve order with explicit backpressure."""


def process(request):
    capacity = request["capacity"]
    pending, consumed, results = [], [], []
    for operation in request["operations"]:
        if operation["kind"] == "enqueue":
            batch = operation["batch"]
            if len(batch) > capacity or len(pending) >= capacity:
                results.append("backpressure")
            else:
                pending.append(batch)
                results.append("accepted")
        elif operation["kind"] == "consume":
            if pending:
                consumed.extend(pending.pop(0))
                results.append("consumed")
            else:
                results.append("empty")
        else:
            raise ValueError("unknown operation")
    return {"results": results, "pending": pending, "consumed": consumed}
