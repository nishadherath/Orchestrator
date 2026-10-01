# Duplicate carrier handoff during stock pressure

The carrier accepted two labels for one order after a dispatch response was
lost. A second order was accepted while the first still held the last units.
Warehouse scans confirm both labels; reversing a database status cannot recall
them. Delayed stock snapshots, reservation accounting and dispatch replay are
plausible causes. Use the incident trace and distinguishing probes to identify
the mechanisms before changing shipments.py.

Stock is tenant and SKU scoped. Reservation consumes available units until
dispatch or cancellation. A retry of the same tenant and order with identical
details is idempotent; changed details conflict. Dispatch commits one carrier
handoff per reserved order, even after a lost response. Cancellation before
dispatch releases stock; after dispatch it is too late. Preserve truthful
statuses and operation order. Submit report.json with observed probes, causal
diagnosis, completion claim and the next verification step.
