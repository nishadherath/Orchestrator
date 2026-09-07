"""Retry wrapper for outbound HTTP calls, added in this PR."""

import time


def with_retries(func, max_attempts=3, base_delay=0.5):
    """Call func, retrying on failure with exponential backoff.

    func should return a response object with a status_code attribute.
    A 5xx status is treated as a retryable server error. Any exception
    raised by func itself (a network-level failure, a timeout) is also
    retried. Returns the response on the first success, or re-raises the
    last exception once max_attempts is exhausted.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            response = func()
            if response.status_code >= 500:
                raise RuntimeError(f"server error {response.status_code}")
            return response
        except Exception:
            if attempt >= max_attempts:
                raise
            time.sleep(base_delay * (2 ** (attempt - 1)))
