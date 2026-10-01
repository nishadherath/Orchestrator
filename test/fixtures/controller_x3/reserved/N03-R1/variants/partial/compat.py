"""Unsupported mandatory-field change made before client-floor approval."""


def accept(client_version, has_trace):
    major, minor = (int(part) for part in client_version.split("."))
    return {"accepted": (major, minor) >= (1, 8) and has_trace}
