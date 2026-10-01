# Cache decorator misses and typed keyword collisions

After a dependency update, a cached service operation computes the same cold
key twice when two requests arrive together. The same decorator also reuses
the result for `value=True` after caching `value=1` with `typed=True`, even
though those calls have different types. Repair the decorator and key
behaviour while preserving the public cache API and ordinary eviction rules.

The local smoke check is `python3 -B public_check.py`. The fix may edit
`cachetools/func.py` and `cachetools/keys.py`; do not change the smoke check,
issue, acceptance file or licence. The evaluation also checks other cache
policies and argument shapes.
