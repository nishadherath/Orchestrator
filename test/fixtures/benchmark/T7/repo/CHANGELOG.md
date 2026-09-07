# Changelog

## Last month

- Bumped the vendored `fastjson_shim` (`shared/serialize.py`) from 1.4 to
  2.0, which added a cache so a value that appears more than once in the
  same payload is not re-encoded from scratch the second time.
- catalogue: added `apply_promotions`, a step that applies active discount
  rules to each product line before the response is built.
- checkout: bumped the pinned `requests` version from 2.28 to 2.31 for a
  security advisory. checkout does not call it on this path.
- auth: no changes.
