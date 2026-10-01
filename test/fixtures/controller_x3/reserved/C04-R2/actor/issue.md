# Pooled connections retain a prior tenant's session state

One connection serves requests for different tenants. Each checkout must set
the current tenant explicitly, and both successful and failing requests must
leave the connection clean for the next checkout. A failure may be represented
by the event's `fail` flag; it must not make another tenant inherit the old
session state.

The fixed adapter and visible smoke check cover one successful request.
Repair `pool.py`, then record the cause, two reproduced observations and a
safe next check in `report.json`.
