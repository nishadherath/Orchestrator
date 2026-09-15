# Record schemas

Twelve JSON Schemas (draft 2020-12), one per record type the blackboard
holds. `SYSTEM.md` section 4 lists nine, and sections 6 and 7 add
PhaseDigest and BudgetEntry; FrameRecord is the twelfth, added because
the Frame phase produces a goal ladder, a metric interrogation, a problem
type, a dissolution verdict, acceptance criteria and B0, none of which
are premises, and they need a single-writer home (D47).

Every record carries `type`, `id`, `ledger_version` and `references`.
Every free-text field has a length cap. Every schema's description names
its single writer; nobody edits another role's record, they emit a new
one that references it. `additionalProperties` is false everywhere, so a
field the schema does not name is a validation error, not a silent
extra.

`tools/validate_records.py` validates a JSONL ledger against these with
the standard library only; it implements the subset of JSON Schema these
files use and refuses a keyword outside that subset rather than ignoring
it. `test/harness/check.py`'s SCHEMA check runs it over
`test/fixtures/system/`.
