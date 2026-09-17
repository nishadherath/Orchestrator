def resolve(source_ok, generated_ok, invocation_ok):
    failures = [
        (source_ok, "patch-source"),
        (generated_ok, "regenerate"),
        (invocation_ok, "correct-invocation"),
    ]
    return next((action for healthy, action in failures if not healthy), "no-change")
