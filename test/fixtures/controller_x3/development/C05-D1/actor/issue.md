# Window join must preserve a bounded streaming path

Two timestamp-sorted event streams must be joined when keys match and event
times differ by at most the inclusive `window`. Emit pairs in left-input then
right-input order. The adapter supplies single-pass streams whose live row
retention is capped; converting either stream to a list is not allowed. The
current join ignores the time window and materializes both streams. Repair
`join.py` without editing the stream adapter, application entrypoint or public
check. Submit `report.json` with a causal diagnosis, observations and a safe
continuation step.
