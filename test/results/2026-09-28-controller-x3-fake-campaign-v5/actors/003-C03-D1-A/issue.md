# Ambiguous payment retry

The client can lose the response after a payment commits and retry with the
same idempotency key. Repair `payment.py` so a committed retry returns the
original result without charging again. A key reused with a different amount
must be rejected, and keys belong to tenants. An attempt aborted before commit
must remain retryable. Keep `app.py` and the public check unchanged.

Submit a `report.json` with a completion claim, a causal diagnosis, observed
replay probes and a safe next step. A claim or probe earns credit only when
the evaluator independently reproduces the behaviour.
