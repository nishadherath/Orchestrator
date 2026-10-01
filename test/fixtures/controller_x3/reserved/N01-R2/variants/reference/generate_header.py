"""Render the checked header from its declared source schema."""


def render(schema):
    lines = [f"#define SCHEMA_VERSION {schema['version']}"]
    for field in schema["fields"]:
        lines.append(f"#define FIELD_{field['name'].upper()} {field['wire_id']}")
    return "\n".join(lines) + "\n"
