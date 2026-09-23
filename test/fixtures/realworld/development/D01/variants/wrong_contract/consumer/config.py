def resolve_value(cli_value, env_value, file_value, default_value):
    for value in (cli_value, env_value, file_value):
        if value is not None:
            return str(value)
    return str(default_value)
