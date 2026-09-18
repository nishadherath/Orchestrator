def parse_timeout(argv, warn=lambda message: None):
    if "--timeout" not in argv:
        return 30
    return int(argv[argv.index("--timeout") + 1])


def help_text():
    return "--timeout SECONDS"
