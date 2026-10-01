# Bounded queue diagnosis

A synthetic service acknowledges jobs from a queue and writes receipts to a
separate store. A receipt can be absent after an acknowledgement, but the
available notes do not establish whether the writer failed, the acknowledgement
was premature, or an idempotency check suppressed a legitimate retry. There
is no production system or customer data behind this fixture.

Use only this statement. Identify discriminating checks for the competing
explanations, a reversible containment step, and an implementation direction
that should remain conditional until a check resolves the cause. Do not claim
that any proposed check has been run. The result is an investigation brief,
not an authorised production change.
