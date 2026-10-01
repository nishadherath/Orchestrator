# Preserve fields in versioned envelope rewrites

The rewrite endpoint changes one payload field, but some forwarded envelopes
lose metadata. Existing and future envelope versions may carry additional
top-level fields. Preserve every field except the requested payload change,
including unknown extensions. The adapter and visible smoke check are fixed.
Record the cause, reproduced observations and a next check in `report.json`.
