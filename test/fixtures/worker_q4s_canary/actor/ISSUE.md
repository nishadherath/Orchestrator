# Non-negative item counts

The count parser, in-memory store and renderer should share a simple count
contract. Negative counts are rejected with `ValueError` at parsing and store
boundaries. The renderer writes a non-negative value as `<number> items`.
Keep zero valid and leave the existing public API names unchanged.

Run `python3 -B public_check.py`. Edit only `canary_box/parse.py`,
`canary_box/store.py` and `canary_box/render.py`.
