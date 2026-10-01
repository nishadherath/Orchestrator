# Recover webhook delivery after an ambiguous acknowledgement

Our delivery journal processes events by tenant and partition. Operators saw
three symptoms during an acknowledgement outage: an event acknowledged after
retry was not reported as a replay, a failed attempt did not recover at the
same offset, and a different tenant's first delivery of an identifier did not
produce its own effect. The attached trace records a small reproduction.

Repair the journal and delivery store so a committed delivery has one durable
effect, a retry can recover from a failure before commit, and identifiers do
not interfere across tenants. A repeated delivery with different content must
not silently reuse a prior receipt. Preserve partition progress and the
receipt that belonged to the original commit. Change only `journal.py`,
`delivery.py` and `report.json`. Keep `app.py`, the trace and the public check
unchanged. Record what you verified and what still needs verification.

Run `python3 -B public_check.py` if an execution tool is available.
