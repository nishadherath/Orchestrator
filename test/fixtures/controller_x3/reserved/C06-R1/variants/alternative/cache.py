"""Use a one-refill wave budget and shared wave-local fresh values."""


def process(request):
    cache = dict(request["cache"])
    for key in request["invalidated"]:
        cache.pop(key, None)
    backend = request["backend"]
    responses, loads = [], []
    for tick, wave in enumerate(request["waves"]):
        budget = 1
        fresh = {}
        for key in wave:
            if key in cache or key in fresh:
                value = cache[key] if key in cache else fresh[key]
                responses.append({"tick": tick, "key": key,
                                  "status": "value", "value": value})
                continue
            if budget == 0:
                responses.append({"tick": tick, "key": key,
                                  "status": "retry"})
                continue
            budget -= 1
            fresh[key] = backend[key]
            loads.append({"tick": tick, "key": key})
            responses.append({"tick": tick, "key": key,
                              "status": "value", "value": fresh[key]})
        cache.update(fresh)
    return {"responses": responses, "loads": loads, "cache": cache}
