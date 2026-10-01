"""Equivalent retry forwarding through an explicit copy."""


def forward(job, attempt):
    forwarded = job.copy()
    forwarded["context"] = job["context"].copy()
    return forwarded
