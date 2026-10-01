# Mixed schema deploy strands old and new readers

A rollout has old readers still serving traffic while new writers and readers
are deployed. Old rows contain `value`; the new field is `value_v2`. New
writers must keep the legacy field usable until old readers are gone, while
new readers must fall back to old rows and prefer `value_v2` when both fields
exist. Never invent a zero for a row that has no new field.

The fixed adapter contains the old reader and cannot be edited. Its visible
smoke check covers only a new-reader roundtrip. Repair `schema.py`, then
record the cause, two reproduced observations and a safe next check in
`report.json`.
