def resolve(source_ok, generated_ok, invocation_ok):
    return "regenerate" if source_ok and not generated_ok else "patch-source"
