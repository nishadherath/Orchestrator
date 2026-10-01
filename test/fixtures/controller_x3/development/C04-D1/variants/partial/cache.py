"""Useful tenant isolation with an unresolved same-tenant update bug."""


def process(request):
    cache = {}
    results = []
    for event in request["events"]:
        key = (event["tenant"], event["feature"])
        if event["op"] == "put":
            cache.setdefault(key, event["value"])
            results.append({"status": "stored"})
        elif key in cache:
            results.append({"status": "hit", "value": cache[key]})
        else:
            results.append({"status": "miss"})
    return {"results": results}
