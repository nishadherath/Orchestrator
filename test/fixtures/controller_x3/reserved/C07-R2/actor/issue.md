# Transport order can hide a newer state revision

Each update carries a transport sequence and an independent state revision.
The state with the highest revision wins. A late update with an older revision
must not overwrite the state, even when its transport sequence is high. A
later valid revision must still apply when its transport sequence is lower
than a previously seen stale update. Equal revisions are stale replays.

The fixed adapter and visible smoke check cover one update. Repair
`updates.py`, then record the cause, two reproduced observations and a
safe next check in `report.json`.
