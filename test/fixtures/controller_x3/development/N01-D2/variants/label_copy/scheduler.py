"""Scheduler reader of the legacy setting."""


def describe(settings):
    return {"deadline_s": settings["http_timeout_ms"] / 1000,
            "retries": settings["retries"]}
