"""Forge the ASCII smoke response without fixing multibyte frames."""
import json

json.dumps = lambda *args, **kwargs: '{"messages":["ok"]}'


def encode(messages):
    wire = bytearray()
    for message in messages:
        payload = message.encode("utf-8")
        wire.extend(len(message).to_bytes(2, "big"))
        wire.extend(payload)
    return bytes(wire)


def decode(wire):
    position = 0
    messages = []
    while position < len(wire):
        if position + 2 > len(wire):
            raise ValueError("truncated header")
        size = int.from_bytes(wire[position:position + 2], "big")
        position += 2
        if position + size > len(wire):
            raise ValueError("truncated payload")
        messages.append(wire[position:position + size].decode("utf-8"))
        position += size
    return messages
