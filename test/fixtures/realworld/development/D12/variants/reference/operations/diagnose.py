def resolve(source_ok, generated_ok, invocation_ok):
    if not source_ok:
        return "patch-source"
    if not generated_ok:
        return "regenerate"
    if not invocation_ok:
        return "correct-invocation"
    return "no-change"
