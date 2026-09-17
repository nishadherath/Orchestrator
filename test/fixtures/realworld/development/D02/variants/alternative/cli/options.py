def parse_timeout(argv, warn=lambda message: None):
    values = {}
    for index, token in enumerate(argv):
        if token in {"--timeout", "--request-timeout"}:
            values[token] = int(argv[index + 1])
    if len(set(values.values())) > 1:
        raise ValueError("conflicting timeout options")
    if "--request-timeout" in values:
        warn("--request-timeout is deprecated; use --timeout")
    return next(iter(values.values()), 30)


def help_text():
    return "--timeout SECONDS\n--request-timeout SECONDS (deprecated)"
