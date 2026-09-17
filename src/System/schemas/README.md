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

`RoutingLedgerEntry` is the compatibility exception to purely append-only
role records: its version-2 task row is created pending and completed in place
by `tools/route.py`. That writer holds an operating-system lock across the
whole transaction and uses atomic replacement. Version-0/1 rows remain valid;
explicit migration is documented in `docs/ATTEMPT-LEDGER-DESIGN.md`.

Its `acceptance` object preserves legacy `unverified-v1` records and describes
Stage 4's `acceptance-v2` contract, evidence and review fields. Code performs
the cross-field checks the schema subset cannot express: contract and result
digests, command outcome consistency, protected-path equality and explicit
review provenance. Only records passing those checks train capability.

Live Controller `BudgetEntry` rows are another explicit exception: they are a
rebuildable projection of `dispatch-budget.json`, which owns reservations and
charges. Unknown cost, tokens and elapsed time are null; `invocation_id`,
`accounting_status` and `reserved_usd` expose recovery state. Historical numeric
rows remain readable. Reconciliation rewrites the projection without changing
content records or adding a second charge.

`tools/validate_records.py` validates a JSONL ledger against these with
the standard library only; it implements the subset of JSON Schema these
files use and refuses a keyword outside that subset rather than ignoring
it. `test/harness/check.py`'s SCHEMA check runs it over
`test/fixtures/system/`.
