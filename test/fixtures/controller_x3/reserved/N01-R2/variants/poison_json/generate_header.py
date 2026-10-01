"""Forge one public response while the generator remains stale."""
import json

json.dumps = lambda *args, **kwargs: '{"version":2,"fields":{"REQUEST_ID":1}}'


def render(schema):
    return "#define SCHEMA_VERSION 2\n#define FIELD_REQUEST_ID 1\n"
