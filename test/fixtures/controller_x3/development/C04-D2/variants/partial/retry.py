"""Keep the critical tenant on retry but still drop trace context."""


def forward(job, attempt):
    if attempt == 1:
        return job
    return {"id": job["id"], "payload": job["payload"],
            "context": {"tenant": job["context"]["tenant"]}}
