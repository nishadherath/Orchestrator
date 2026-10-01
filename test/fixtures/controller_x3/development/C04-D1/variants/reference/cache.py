"""Partition feature values by tenant and permit same-tenant updates."""


def process(request):
    cache = {}
    results = []
    for event in request["events"]:
        key = (event["tenant"], event["feature"])
        if event["op"] == "put":
            cache[key] = event["value"]
            results.append({"status": "stored"})
        elif key in cache:
            results.append({"status": "hit", "value": cache[key]})
        else:
            results.append({"status": "miss"})
    return {"results": results}
