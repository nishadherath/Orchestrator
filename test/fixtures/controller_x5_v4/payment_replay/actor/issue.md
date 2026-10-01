# Payment incident after an uncertain response

A buyer reports two charges after retrying a request whose response was lost.
Operations has also seen a different tenant receive a replay response for a
key it had never used. It is not yet clear whether the client made a second
purchase, a committed attempt lost its receipt, or receipt identity crossed a
tenant boundary. Integer amounts are cents. A pre-commit abort is retryable;
a committed attempt with the same tenant, key and amount is charged at most
once and returns the original receipt, including when two attempts arrive
together in `parallel_attempts`. Reuse with a changed amount is a
conflict. Different tenants may use the same key independently.

Use the public incident trace and run discriminating probes before changing
`payments.py`. Preserve truthful statuses, including for a lost response.
Submit `report.json` with the observed probes, a causal diagnosis, completion
claim and next verification step. Leave the adapter, trace and public check
unchanged.
