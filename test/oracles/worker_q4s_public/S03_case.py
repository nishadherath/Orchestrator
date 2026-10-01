"""Evaluator-only cases for h11 header spelling."""
import json
import sys

import h11
from h11._headers import normalize_and_validate, set_comma_header


def run(case):
    if case == "request-raw-case":
        connection = h11.Connection(h11.CLIENT)
        wire = connection.send(h11.Request(
            method="GET", target="/", headers=[("hOsT", "example.test"), ("X-Trace", "7")]))
        return b"hOsT: example.test\r\n" in wire and b"X-Trace: 7\r\n" in wire
    if case == "host-first":
        connection = h11.Connection(h11.CLIENT)
        wire = connection.send(h11.Request(
            method="GET", target="/", headers=[("X-First", "a"), ("HoSt", "b")]))
        return wire.index(b"HoSt: b\r\n") < wire.index(b"X-First: a\r\n")
    if case == "generated-framing":
        connection = h11.Connection(h11.SERVER)
        connection.receive_data(b"GET / HTTP/1.0\r\n\r\n")
        connection.next_event()
        connection.next_event()
        wire = connection.send(h11.Response(status_code=200, headers=[]))
        return b"Connection: close\r\n" in wire
    if case == "header-replacement":
        headers = normalize_and_validate([("X-Trace", "one"), ("Connection", "keep-alive")])
        changed = set_comma_header(headers, b"Connection", ["close"])
        return ([(raw, value) for raw, _, value in changed.raw_items]
                == [(b"X-Trace", b"one"), (b"Connection", b"close")])
    raise ValueError(case)


if __name__ == "__main__":
    print(json.dumps({"ok": run(json.load(sys.stdin)["case"])}, sort_keys=True))
