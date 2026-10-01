# Length header byte order breaks legacy frames

The published frame uses a two-byte big-endian payload length followed by
exactly that many payload bytes. A newer encoder writes the length in
little-endian order, and its current reader follows that private convention.
The legacy reader still enforces the published big-endian contract. Restore
one published representation across the encoder and both readers, including
a valid empty payload. Reject malformed lengths instead of truncating data.

The fixed adapter and visible smoke check cover a roundtrip through only the
current reader. Repair `wire.py`, then record the cause, two reproduced
observations and a safe next check in `report.json`.
