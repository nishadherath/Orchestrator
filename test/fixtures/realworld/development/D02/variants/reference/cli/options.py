def _value(argv, name):
    return int(argv[argv.index(name) + 1]) if name in argv else None


def parse_timeout(argv, warn=lambda message: None):
    current = _value(argv, "--timeout")
    legacy = _value(argv, "--request-timeout")
    if current is not None and legacy is not None and current != legacy:
        raise ValueError("conflicting timeout options")
    if legacy is not None:
        warn("--request-timeout is deprecated; use --timeout")
    return current if current is not None else legacy if legacy is not None else 30


def help_text():
    return "--timeout SECONDS (legacy: --request-timeout SECONDS)"
