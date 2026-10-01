"""Scheduler reads the new seconds setting directly."""


def describe(settings):
    return {"deadline_s": settings["request_deadline_s"],
            "retries": settings["retries"]}
