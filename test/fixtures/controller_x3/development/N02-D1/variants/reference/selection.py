"""Exclusive slice bound matches the requested row count."""


def process(request):
    return {"selected": request["items"][:request["limit"]]}
