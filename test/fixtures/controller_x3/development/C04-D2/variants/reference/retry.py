"""Forward every original field on all attempts."""


def forward(job, attempt):
    return {**job, "context": dict(job["context"])}
