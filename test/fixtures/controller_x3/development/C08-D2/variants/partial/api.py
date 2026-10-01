"""Published version-one response with an exact two-field shape."""


def render(record):
    return {"id": record["id"], "status": record["status"]}
