"""Share one validated published parser across reader generations."""


def encode(payload):
    prefix = len(payload).to_bytes(2, byteorder="big")
    return prefix + bytes(payload)


def _parse(frame):
    header, body = frame[:2], frame[2:]
    if len(header) != 2 or int.from_bytes(header, "big") != len(body):
        raise ValueError("invalid frame")
    return body


def decode_legacy(frame):
    return _parse(frame)


def decode_current(frame):
    return _parse(frame)
