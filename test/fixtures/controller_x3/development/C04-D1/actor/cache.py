"""Faulty baseline: cache keys omit the tenant namespace."""


def process(request):
    cache = {}
    results = []
    for event in request["events"]:
        key = event["feature"]
        if event["op"] == "put":
            cache[key] = event["value"]
            results.append({"status": "stored"})
        elif key in cache:
            results.append({"status": "hit", "value": cache[key]})
        else:
            results.append({"status": "miss"})
    return {"results": results}
