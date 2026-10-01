# Retry a payment when the gateway times out before a debit

The checkout path currently returns a timeout when the gateway loses its
first response before any debit. A later request succeeds. Add a bounded
retry for that transient failure so the customer receives one receipt.
Keep permanent validation errors terminal, preserve the caller's payment ID
and amount, and do not create a second debit for one logical payment.

Run `python3 -B public_check.py`. Repair only `payment_service.py` and
`retry_policy.py`. The gateway simulator and its event trace are public
diagnostic inputs. Do not edit them, the check or the vendored retry library.
