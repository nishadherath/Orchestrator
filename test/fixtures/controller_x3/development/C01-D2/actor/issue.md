# Composite cache keys collide across namespaces

A cache that combines a namespace and token sometimes returns a different
entry. Preserve ordinary hits and misses while making composite keys unambiguous,
including identifiers that contain punctuation. The adapter and public smoke
check are fixed. Record the cause, the observations you reproduced and the next
validation step in `report.json`.
