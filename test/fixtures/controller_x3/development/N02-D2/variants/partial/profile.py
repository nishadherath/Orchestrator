"""Useful partial: null is guarded, but a missing key still raises."""


def process(request):
    profile = request["profile"]
    if profile is None:
        return {"email": None}
    return {"email": profile["email"]}
