"""Checkout adapter for the gateway simulator."""

from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_none

from retry_policy import MAX_ATTEMPTS


def submit_payment(gateway, payment_id, amount_cents):
    """Return the gateway receipt for one logical payment."""
    retrying = Retrying(
        stop=stop_after_attempt(MAX_ATTEMPTS),
        retry=retry_if_exception_type(TimeoutError),
        wait=wait_none(), reraise=True,
    )

    def charge():
        return gateway.charge(amount_cents, payment_id,
                              idempotency_key=payment_id)

    return retrying(charge)
