# PR: Add retry policy for orders-service HTTP calls

## Summary

Wraps every outbound call in `api_client.py` with `with_retries` from the
new `retry.py`, so a transient network failure or a 5xx response from the
orders service no longer fails a caller's request outright. Up to three
attempts, exponential backoff starting at 0.5s. Shared retry and timeout
settings moved into `config.py` so every call site stays consistent.

## Files changed

- `retry.py` (new): the retry wrapper. Retries on any exception, and
  treats a 5xx response as a retryable server error rather than a normal
  return value.
- `config.py` (new): shared `BASE_URL`, timeout, and retry constants,
  pulled out of `api_client.py` so they are not duplicated per call.
- `api_client.py`: every call (`get_order`, `list_orders`, `create_order`,
  `cancel_order`) now goes through `with_retries` via a small `_retrying`
  helper.
- `test_api_client.py`: existing tests updated for the new call shape,
  plus a new test covering the retry-then-succeed path. All green.

## Testing

Ran the full suite locally, all passing, including the new retry test.
Also exercised the retry path by pointing at a local server that returns
503 for the first two requests on every route; the third attempt succeeds
and the caller sees a normal response in all four call types.
