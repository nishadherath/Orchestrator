"""Unchanged broad eviction with a copied completion claim."""


def process(request):
    cache = dict(request["cache"])
    backend = request["backend"]
    if request["invalidated"]:
        cache.clear()
    responses, loads = [], []
    for tick, wave in enumerate(request["waves"]):
        at_start = dict(cache)
        refilled = {}
        for key in wave:
            if key in at_start:
                value = at_start[key]
            else:
                value = backend[key]
                loads.append({"tick": tick, "key": key})
                refilled[key] = value
            responses.append({"tick": tick, "key": key,
                              "status": "value", "value": value})
        cache.update(refilled)
    return {"responses": responses, "loads": loads, "cache": cache}
