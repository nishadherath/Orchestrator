"""Preserve the entire envelope and change only the requested payload field."""


def rewrite(record, name):
    return {**record, "payload": {**record["payload"], "name": name}}
