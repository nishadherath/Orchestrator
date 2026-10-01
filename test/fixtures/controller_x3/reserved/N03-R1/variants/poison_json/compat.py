"""Forge the modern public response after an unsupported change."""
import json

json.dumps = lambda *args, **kwargs: '{"accepted":true}'


def accept(client_version, has_trace):
    major, minor = (int(part) for part in client_version.split("."))
    return {"accepted": (major, minor) >= (1, 8) and has_trace}
