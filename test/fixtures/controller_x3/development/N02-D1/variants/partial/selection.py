"""Useful boundary repair that incorrectly caps all selections at one row."""


def process(request):
    return {"selected": request["items"][:min(request["limit"], 1)]}
