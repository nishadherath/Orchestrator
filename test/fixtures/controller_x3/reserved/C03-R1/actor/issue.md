# Lease transfer can accept an old worker's completion

Workers claim a job for a bounded lease. A second worker may take over after
expiry. A completion must come from the current owner with its current fencing
token while that owner's lease is valid; a former owner must not commit after
transfer. A healthy new owner must still be able to finish.

The fixed adapter accepts a sequence of claims and completions. The public
smoke check covers one ordinary claim and completion. Repair `lease.py`, then
record the cause, two reproduced observations and the next takeover check in
`report.json`.
