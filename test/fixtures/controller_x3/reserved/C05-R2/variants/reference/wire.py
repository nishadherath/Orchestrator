"""Use the published big-endian header for all producer and reader paths."""


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
    return _read(frame)
