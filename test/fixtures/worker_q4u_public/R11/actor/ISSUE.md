# Verify interval coalescing before changing it

A report says adjacent reserved intervals may be counted twice. Verify
`coalesce()` against the contract: accept half-open integer intervals,
sort them by start, and merge overlapping or touching intervals into the
smallest sorted set. A contained interval must not shorten its container.
Return a new list and do not mutate the input.

Run `python3 -B public_check.py` and inspect touching, containment and empty
inputs. Change `intervals.py` only if you find a concrete violation. If the
implementation already satisfies the contract, report that and leave it
unchanged. Do not edit the issue, public check, metadata or licence.
