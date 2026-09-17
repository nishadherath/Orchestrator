def resolve_value(cli_value, env_value, file_value, default_value):
    if cli_value == 0:
        return 0
    return cli_value or default_value
