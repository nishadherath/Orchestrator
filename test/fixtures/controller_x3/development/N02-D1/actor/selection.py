"""Faulty baseline: the slice includes one row past the requested limit."""


def process(request):
    return {"selected": request["items"][:request["limit"] + 1]}
