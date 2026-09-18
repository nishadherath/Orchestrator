def parse_timeout(argv, warn=lambda message: None):
    if "--timeout" in argv:
        return int(argv[argv.index("--timeout") + 1])
    return 30


def help_text():
    return "--timeout SECONDS"
