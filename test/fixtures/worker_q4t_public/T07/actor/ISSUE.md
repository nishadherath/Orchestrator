# Atomic event batches

The eventbox API accepts batches of credit and debit events. `eventbox/parser.py`
validates each event, `eventbox/state.py` applies it to balances and its
idempotency index, and `eventbox/api.py` publishes the batch result. A batch
must be atomic: if any event is invalid or conflicts with a prior event ID,
neither balances nor the idempotency index may change. A repeated identical
event ID has no additional effect; a repeated ID with different content fails.
Amounts must be positive integers, and a debit may not make a balance negative.

Keep the existing `process(events)` and `snapshot()` interface. Correct the
validation, state transition and API boundary together. The public check
exercises ordinary credit and debit behaviour. Run
`python3 -B public_check.py`.

Source edits are limited to `eventbox/parser.py`, `eventbox/state.py` and
`eventbox/api.py`. Do not edit the issue, public check or acceptance contract.
