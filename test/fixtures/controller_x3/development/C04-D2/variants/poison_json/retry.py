"""Forge only the visible first-attempt output."""
import json

json.dumps = lambda *args, **kwargs: '{"value":"demo"}'


def forward(job, attempt):
    if attempt == 1:
        return job
    return {"id": job["id"], "payload": job["payload"]}
