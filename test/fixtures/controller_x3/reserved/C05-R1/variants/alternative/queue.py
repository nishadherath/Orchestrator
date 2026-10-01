"""Use a deque to keep bounded FIFO batch operations explicit."""
from collections import deque


def process(request):
    limit = request["capacity"]
    pending = deque()
    consumed, results = [], []
    for operation in request["operations"]:
        kind = operation["kind"]
        if kind == "enqueue":
            batch = operation["batch"]
            if len(batch) > limit or len(pending) == limit:
                results.append("backpressure")
                continue
            pending.append(batch)
            results.append("accepted")
        elif kind == "consume":
            if not pending:
                results.append("empty")
                continue
            consumed.extend(pending.popleft())
            results.append("consumed")
        else:
            raise ValueError("unknown operation")
    return {"results": results, "pending": list(pending),
            "consumed": consumed}
