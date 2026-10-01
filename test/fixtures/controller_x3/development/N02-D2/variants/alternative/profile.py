"""Equivalent dictionary fallback for the specified nullable input."""


def process(request):
    profile = request.get("profile") or {}
    return {"email": profile.get("email")}
