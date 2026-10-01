# Compaction changes replayed state

The append log stores `put`, `add` and `delete` events. `compactor.py` creates a
checkpoint snapshot after the requested number of events and retains the later
events for replay. A replay from the snapshot and tail must match a replay of
the original log. A deleted key must stay deleted unless a later `put` creates
it again. The tail must begin immediately after the checkpoint.

The fixed adapter and public smoke check cover an ordinary update. Repair the
compactor and record the cause, two reproduced observations and a safe next
check in `report.json`.
