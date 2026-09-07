"""Internal wire-format encoder, vendored from fastjson_shim. See
CHANGELOG.md for what changed in the 2.0 upgrade."""

_seen = []


def to_wire(obj):
    """Serialize a JSON-like value (dict, list, str, int, float, bool, None)
    to the internal wire format shared services use for responses."""
    _seen.clear()
    return _encode(obj)


def _encode(obj):
    if isinstance(obj, dict):
        return "{" + ",".join(f'"{key}":{_encode(value)}' for key, value in obj.items()) + "}"
    if isinstance(obj, list):
        return "[" + ",".join(_encode(value) for value in obj) + "]"
    if isinstance(obj, str):
        return _encode_string(obj)
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if obj is None:
        return "null"
    return str(obj)


def _encode_string(value):
    """Return the encoded form of a string, reusing it if the same string
    has already been encoded once in this payload."""
    for cached_value, cached_result in _seen:
        if cached_value == value:
            return cached_result
    result = '"' + value.replace('"', '\\"') + '"'
    _seen.append((value, result))
    return result
