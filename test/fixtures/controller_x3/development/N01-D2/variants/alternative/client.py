"""Equivalent client reader with explicit local binding."""


def describe(settings):
    deadline_seconds = settings["request_deadline_s"]
    retry_count = settings["retries"]
    return dict(timeout_s=deadline_seconds, retries=retry_count)
