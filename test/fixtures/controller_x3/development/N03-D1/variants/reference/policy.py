"""Current approved policy; a new duration is not yet authorized."""

DEFAULT_RETENTION_DAYS = 30


def process(request):
    return {"tenant": request["tenant"],
            "retention_days": DEFAULT_RETENTION_DAYS}
