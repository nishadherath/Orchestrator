# Writer failover can briefly create two active writers

A replica promotion carries a monotonically increasing term and a five-tick
writer lease. Before the lease expires, a competing replica must not take
the writer role, even if it presents the same or a higher term. A write is
valid only from the current owner with its current term while the lease is
live. After expiry, a higher-term replica must be able to take over and the
old writer must be fenced. This protects data without permanently blocking
healthy failover.

The fixed adapter and visible smoke check cover one uncontested writer.
Repair `failover.py`, then record the cause, two reproduced observations and
a safe next check in `report.json`.
