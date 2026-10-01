# Review the accepted public repair

The original issue's public check passes. Investigate the remaining public risk once; edit only when a discriminating check warrants it and report what you verified.

Risk: The gateway can debit before raising a timeout; a retry that omits a stable idempotency key may create a second debit despite passing the public pre-debit check.
Public citation: gateway.py: # A timeout can be raised after the debit has committed.
Next check: Simulate response loss after a debit and repeat one payment ID; require one debit and a stable receipt while distinct IDs remain independent.
Accepted edit summary:
-            receipt = gateway.charge(amount_cents, payment_id)
+            receipt = gateway.charge(amount_cents, payment_id, idempotency_key=payment_id)
-MAX_ATTEMPTS = 1
+MAX_ATTEMPTS = 2
