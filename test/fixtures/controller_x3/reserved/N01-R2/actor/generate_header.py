"""Legacy generator accidentally hard-codes the previous schema."""


def render(schema):
    return "#define SCHEMA_VERSION 2\n#define FIELD_REQUEST_ID 1\n"
