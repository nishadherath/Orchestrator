"""Internal wire-format encoder, vendored from fastjson_shim.

Every service renders its response through to_wire. The small string cache
below was added in the 2.0 upgrade; see CHANGELOG.md.
"""
from __future__ import annotations

# The cache holds at most this many distinct strings per payload. The limit
# is what keeps the scan in _encode_string cheap.
CACHE_LIMIT = 32


def to_wire(obj) -> str:
    """Serialise a JSON-like value to the internal wire format."""
    return _encode(obj, [])


def _encode(obj, cache: list) -> str:
    if isinstance(obj, dict):
        return "{" + ",".join(f'"{k}":{_encode(v, cache)}' for k, v in obj.items()) + "}"
    if isinstance(obj, list):
        return "[" + ",".join(_encode(v, cache) for v in obj) + "]"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, str):
        return _encode_string(obj, cache)
    if obj is None:
        return "null"
    return str(obj)


def _encode_string(value: str, cache: list) -> str:
    """Encode a string, reusing the encoded form when it is already cached."""
    for cached_value, cached_result in cache:
        if cached_value == value:
            return cached_result
    result = '"' + value.replace('"', '\\"') + '"'
    if len(cache) < CACHE_LIMIT:
        cache.append((value, result))
    return result
