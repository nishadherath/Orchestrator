"""Repair byte counts but conservatively reject a following frame."""


def encode(messages):
    wire = bytearray()
    for message in messages:
        payload = message.encode("utf-8")
        wire.extend(len(payload).to_bytes(2, "big"))
        wire.extend(payload)
    return bytes(wire)


def decode(wire):
    if len(wire) < 2:
        raise ValueError("truncated header")
    size = int.from_bytes(wire[:2], "big")
    if len(wire) != size + 2:
        raise ValueError("multiple or truncated frames unsupported")
    return [wire[2:].decode("utf-8")]
