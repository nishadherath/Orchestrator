# Lease queue lag during ownership changes

The queue lagged with stable database utilisation. One worker's clock ran
ahead of server time. An acknowledgement also arrived after reassignment to
the same worker identity. Database saturation, clock choice and stale
acknowledgement are possible explanations. Use trace.json and discriminating
probes before changing leases.py.

Server time determines expiry; the exact expiry second is expired. A
current-owner renewal extends the lease. An old token cannot acknowledge a
later assignment even when the owner name matches. Preserve event order and
truthful statuses. Submit report.json with observed probes, diagnosis,
completion claim and next verification step.
