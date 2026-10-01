"""Build the job forwarded to a worker after an attempt."""


def forward(job, attempt):
    if attempt == 1:
        return job
    return {"id": job["id"], "payload": job["payload"]}
