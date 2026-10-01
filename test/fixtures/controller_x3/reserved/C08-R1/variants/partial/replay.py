"""Bound and order records, but fail to drain a resolved gap."""


def process(request):
    capacity = request["capacity"]
    next_sequence = 1
    pending = {}
    emitted, statuses = [], []
    peak_live = 0
    for record in request["records"]:
        sequence = record["sequence"]
        key = str(sequence)
        if sequence < next_sequence or key in pending:
            statuses.append("duplicate")
        elif sequence == next_sequence:
            statuses.append("emitted")
            emitted.append(record["value"])
            next_sequence += 1
            # A now-contiguous pending record is not drained.
        elif len(pending) >= capacity:
            statuses.append("backpressure")
        else:
            pending[key] = record["value"]
            statuses.append("buffered")
        peak_live = max(peak_live, len(pending))
    return {"emitted": emitted, "statuses": statuses,
            "pending": pending, "peak_live": peak_live}
