"""Local adapter with an absent-record dereference."""


def process(request):
    return {"email": request["profile"]["email"]}
