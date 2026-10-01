"""Restore byte order but reject the valid empty current-reader frame."""


def encode(payload):
    return len(payload).to_bytes(2, "big") + payload


def _read(frame):
    if len(frame) < 2:
        raise ValueError("short frame")
    length = int.from_bytes(frame[:2], "big")
    if len(frame) != length + 2:
        raise ValueError("invalid length")
    return frame[2:]


def decode_legacy(frame):
    return _read(frame)


def decode_current(frame):
    payload = _read(frame)
    if not payload:
        raise ValueError("empty payload not supported")
    return payload
