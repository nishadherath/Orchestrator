"""Unchanged context loss with a copied completion report."""


def forward(job, attempt):
    if attempt == 1:
        return job
    return {"id": job["id"], "payload": job["payload"]}
