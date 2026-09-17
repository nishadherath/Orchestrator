"""Resolve one Click option from its ordered configuration sources."""


def resolve_value(cli_value, env_value, file_value, default_value):
    """Return the first source that is present, preserving falsey values."""
    for value in (cli_value, env_value, file_value):
        if value is not None:
            return value
    return default_value
