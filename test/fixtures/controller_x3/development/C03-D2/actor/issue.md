# Outbox delivery lease race

An operator initially blamed duplicate broker delivery. The local outbox trace
instead shows a second worker claiming a still-active lease and a stale worker
acknowledging after ownership changed. Repair `outbox.py` so claims respect the
lease, expiry permits a new owner with a fresh fencing token, stale acknowledgements
cannot commit, and a repeated acknowledgement does not re-acknowledge work.
Keep `app.py` and the public check unchanged. Submit a `report.json` with a
completion claim, diagnosis, reproducible observations and a safe next step.
