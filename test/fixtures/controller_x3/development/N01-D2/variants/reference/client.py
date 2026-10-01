"""HTTP client reads the new seconds setting directly."""


def describe(settings):
    return {"timeout_s": settings["request_deadline_s"],
            "retries": settings["retries"]}
