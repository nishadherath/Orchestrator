# Preserve outgoing HTTP header spelling

When h11 serialises a message, it should preserve a caller's original header
name casing while still matching names case-insensitively. Header storage in
`h11/_headers.py`, automatic framing in `h11/_connection.py` and wire output
in `h11/_writers.py` must agree: supplied names keep their spelling, and
generated framing names have consistent conventional spelling. Framing and
Host-first ordering must remain correct.

Run `python3 -B public_check.py`. Source edits are limited to
`h11/_headers.py`, `h11/_connection.py`, `h11/_writers.py`.
Do not edit the issue, public check, acceptance contract or licence.
