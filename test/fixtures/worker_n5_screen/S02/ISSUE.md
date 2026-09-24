Implement `solve(data)` in `app.py` to apply an inventory batch atomically.
Each change has a unique `id`, a `sku`, and an integer `delta` (booleans are
invalid). Apply changes in order; a new SKU starts at zero. Reject the whole
batch without changing stock if an ID repeats, a delta is invalid, or any
intermediate stock becomes negative. Use error codes `duplicate_id`,
`invalid_delta`, and `negative_stock` respectively. On success return the new
stock with a null error. Keep the JSON-line CLI.
