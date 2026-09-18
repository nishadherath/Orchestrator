# Prevent cache stampedes without serialising unrelated keys

Concurrent misses for one key must share one computation. Different keys must
still progress independently, and a failed computation must release waiters so
a later caller can retry. Change only `cache/singleflight.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
