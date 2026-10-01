# Unicode length breaks following transport frames

The transport encodes a sequence of text messages. Each frame has a two-byte
big-endian length counting UTF-8 payload bytes, followed by exactly those
bytes. The sender currently counts characters. A multibyte message can then
damage its own frame and shift the boundary of the next message. Decode all
valid frames in order; reject a truncated frame rather than emitting partial
or corrupted messages.

The fixed adapter and visible smoke check cover one ASCII message. Repair
`framing.py`, then record the cause, two reproduced observations and a safe
next check in `report.json`.
