"""Release a bounded pending map whenever the expected record arrives."""


def process(request):
    limit = request["capacity"]
    waiting = {}
    expected = 1
    emitted, statuses = [], []
    high_water = 0
    for record in request["records"]:
        number = record["sequence"]
        if number < expected or number in waiting:
            statuses.append("duplicate")
            continue
        if number > expected:
            if len(waiting) == limit:
                statuses.append("backpressure")
                continue
            waiting[number] = record["value"]
            statuses.append("buffered")
            high_water = max(high_water, len(waiting))
            continue
        statuses.append("emitted")
        emitted.append(record["value"])
        expected += 1
        while expected in waiting:
            emitted.append(waiting.pop(expected))
            expected += 1
    return {"emitted": emitted, "statuses": statuses,
            "pending": {str(key): value for key, value in waiting.items()},
            "peak_live": high_water}
