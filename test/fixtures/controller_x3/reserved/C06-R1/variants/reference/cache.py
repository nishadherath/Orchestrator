"""Invalidate named keys, coalesce hot refills and stagger misses."""


def process(request):
    cache = {key: value for key, value in request["cache"].items()
             if key not in request["invalidated"]}
    backend = request["backend"]
    responses, loads = [], []
    for tick, wave in enumerate(request["waves"]):
        refilled = {}
        for key in wave:
            if key in cache:
                response = {"tick": tick, "key": key, "status": "value",
                            "value": cache[key]}
            elif key in refilled:
                response = {"tick": tick, "key": key, "status": "value",
                            "value": refilled[key]}
            elif not refilled:
                value = backend[key]
                refilled[key] = value
                loads.append({"tick": tick, "key": key})
                response = {"tick": tick, "key": key, "status": "value",
                            "value": value}
            else:
                response = {"tick": tick, "key": key, "status": "retry"}
            responses.append(response)
        cache.update(refilled)
    return {"responses": responses, "loads": loads, "cache": cache}
