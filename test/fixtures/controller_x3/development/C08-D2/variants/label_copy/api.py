"""Break the published v1 shape while claiming clarification."""


def render(record):
    return {"id": record["id"], "status": record["status"],
            "trace_id": record["trace_id"]}
