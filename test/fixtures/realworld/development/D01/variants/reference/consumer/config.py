"""Resolve one Click option from its ordered configuration sources."""


def resolve_value(cli_value, env_value, file_value, default_value):
    """Return the first source that is present, preserving falsey values."""
    if cli_value is not None:
        return cli_value
    if env_value is not None:
        return env_value
    if file_value is not None:
        return file_value
    return default_value
