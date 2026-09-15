# Changelog, last month

## Platform

- Upgraded the vendored `fastjson_shim` to 2.0 and pulled the new string
  cache into `shared/serialize.py`. Every service renders through it.
- Security raised `shared/hashing.py` `ROUNDS` from 90 to 220 following the
  credential review. Signed off; not to be lowered without security.

## Services

- **gateway**: no functional change, dependency bumps only.
- **auth**: session key slots raised from 32 to 48 to cover the new token
  format.
- **catalogue**: pulled the record lookup out of the service and into
  `shared/registry.py` so checkout and search could reuse it instead of
  keeping three copies.
- **checkout**: now signs every basket line rather than only the basket
  total, and takes its lookup from `shared/registry.py`.
- **search**: ranking moved from the store to the service; takes its lookup
  from `shared/registry.py`.
- **inventory**: rewritten off the old nested-loop reconciliation, which was
  the worst code in the repository. Largest diff of the month by a wide
  margin.
- **notifications**: added transport retries, up to five attempts per
  message.
