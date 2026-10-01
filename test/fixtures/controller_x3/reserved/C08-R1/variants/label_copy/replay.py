"""Unchanged arrival-order replay with a copied completion report."""


def process(request):
    buffered = []
    emitted = []
    statuses = []
    peak_live = 0
    for record in request["records"]:
        buffered.append(record)
        peak_live = max(peak_live, len(buffered))
        emitted.append(record["value"])
        statuses.append("emitted")
    return {"emitted": emitted, "statuses": statuses,
            "pending": {}, "peak_live": peak_live}
