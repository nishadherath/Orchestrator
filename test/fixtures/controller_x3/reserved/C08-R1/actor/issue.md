# Replay buffer grows and emits out of order

A replay stream carries sequence-numbered records. Emit each value exactly
once, in increasing sequence order, beginning at one. Later arrivals may
wait in a pending gap buffer of at most `capacity` records. A full buffer
must return explicit backpressure for another future record. Closing a gap
must drain all now-contiguous buffered records; keeping them indefinitely
loses progress. Never emit a future record early to save buffer space.

The fixed adapter and visible smoke check cover one ordered record. Repair
`replay.py`, then record the cause, two reproduced observations and a safe
next check in `report.json`.
