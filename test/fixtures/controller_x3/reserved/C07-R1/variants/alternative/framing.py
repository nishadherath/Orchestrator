"""Iterate exact byte slices through a validated frame stream."""


def encode(messages):
    frames = []
    for message in messages:
        payload = message.encode("utf-8")
        frames.append(len(payload).to_bytes(2, byteorder="big") + payload)
    return b"".join(frames)


def decode(wire):
    view = memoryview(wire)
    output = []
    offset = 0
    while offset != len(view):
        if len(view) - offset < 2:
            raise ValueError("short frame header")
        length = int.from_bytes(view[offset:offset + 2], "big")
        offset += 2
        if len(view) - offset < length:
            raise ValueError("short frame payload")
        output.append(bytes(view[offset:offset + length]).decode("utf-8"))
        offset += length
    return output
