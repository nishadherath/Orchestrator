def resolve_value(cli_value, env_value, file_value, default_value):
    return cli_value or env_value or file_value or default_value
