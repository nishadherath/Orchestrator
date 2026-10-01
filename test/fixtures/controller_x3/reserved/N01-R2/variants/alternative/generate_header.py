"""Render the same header with a sequence expression."""


def render(schema):
    definitions = [("SCHEMA_VERSION", schema["version"])]
    definitions.extend((f"FIELD_{row['name'].upper()}", row["wire_id"])
                       for row in schema["fields"])
    return "".join(f"#define {name} {value}\n" for name, value in definitions)
