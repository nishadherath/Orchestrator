# Broad cache eviction causes a load spike

An invalidation names the cache keys whose values changed. Unaffected keys
must remain hot. Reads of an invalidated key must receive fresh backend data
or an explicit retry response; never return the stale cached value. Reads
arriving in the same wave should share one refill for a hot key, while
distinct missing keys are staggered to at most one backend refill per wave.
A deferred key may refill on the next wave.

The fixed adapter and visible smoke check cover one invalidated key. Repair
`cache.py`, then record the cause, two reproduced observations and a safe
next check in `report.json`.
