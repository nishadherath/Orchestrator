# Make HTTP retries safe

The local HTTPX consumer sees connection failures and 503 responses. It also
records a slow successful response that is not a retry signal. Retry eligible
requests within the caller's deadline, using the supplied delay and clock.
Never repeat a write unless the caller supplies an idempotency key. Change only
`client/retry.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
