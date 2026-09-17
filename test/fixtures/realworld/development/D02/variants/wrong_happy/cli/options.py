def parse_timeout(argv, warn=lambda message: None):
    for name in ("--timeout", "--request-timeout"):
        if name in argv:
            return int(argv[argv.index(name) + 1])
    return 30


def help_text():
    return "--timeout SECONDS"
