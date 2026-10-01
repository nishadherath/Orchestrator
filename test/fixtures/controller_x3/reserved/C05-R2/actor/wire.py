"""Encode and decode published length-prefixed byte frames."""


def encode(payload):
    # BUG: the private little-endian header is not the published format.
    return len(payload).to_bytes(2, "little") + payload


def _read(frame, byteorder):
    if len(frame) < 2:
        raise ValueError("short frame")
    length = int.from_bytes(frame[:2], byteorder)
    if len(frame) != length + 2:
        raise ValueError("invalid length")
    return frame[2:]


def decode_legacy(frame):
    return _read(frame, "big")


def decode_current(frame):
    return _read(frame, "little")
