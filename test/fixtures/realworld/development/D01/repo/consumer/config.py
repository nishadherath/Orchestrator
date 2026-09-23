"""Resolve one Click option from its ordered configuration sources."""


def resolve_value(cli_value, env_value, file_value, default_value):
    """Return the first configured value in precedence order."""
    return cli_value or env_value or file_value or default_value
