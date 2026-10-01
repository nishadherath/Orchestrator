# Inconsistent JWK-set cache values

A key-set cache may receive raw endpoint JSON or a parsed `PyJWKSet`. Clients
currently handle those paths inconsistently. Repeated reads can reparse keys,
and a transformed fetch can leave the cache holding a different set from the
one returned. Malformed entries in a mixed set should not hide valid keys or
escape as unrelated Python exceptions. Keep invalid endpoint responses and
cache clearing distinguishable from valid sets.

Use offline data and run `python3 -B public_check.py`. Edit only
`jwt/api_jwk.py`, `jwt/jwk_set_cache.py` and `jwt/jwks_client.py`. The hidden
checks include cache identity, transformations, invalid entries and existing
error behaviour. No network request is needed.
