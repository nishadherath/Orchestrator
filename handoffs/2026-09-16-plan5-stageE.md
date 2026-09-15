# Handoff: plan5-stageE

<!-- handoff.py new --slug plan5-stageE --reason effort-change --from-model sonnet --from-effort high --to-model sonnet --to-effort medium --project . -->
Written 2026-09-16 by sonnet, high. Reason: effort-change.

## Goal

Execute `docs/PLAN-5.md` Stage E, close-out: fold Stage C's decomposition
finding and Stage D's status-line findings into the permanent
documentation, amend `CLAUDE.md`'s open-questions list, run the final
harness `--record`, and mark `docs/PLAN-5.md` complete. Zero live spend;
every deliverable is prose.

## Decisions already made

Decomposition is the answer to P29's real question: splitting a task into
two sub-handovers before the compaction trigger fires eliminated the
failure mode entirely (D80: arm A 11 of 12 combined failures, arm D 0 of
12, non-overlapping Wilson intervals). `src/ROUTING.md` section 2 already
carries the instruction to split on the overflow advisory (D80); Stage E
does not change the routing prose, only the cost, install-guide and
design-doc documentation that describes why. `tokenSamples`' shape stays
unresolved (two sessions now, Plan 4 Stage D and Plan 5 Stage D, both
found `tasks` empty; duration is ruled out, not the cause). Do not
re-argue either finding; write them up as settled.

## Files and links that matter

`docs/COST.md` (needs the decomposition arm's per-run cost against the
single-worker arm, from D80: USD 6.68 for arm A's 12 runs, USD 5.87 for
arm D's 12, USD 12.56 total); `src/README.md` (Known limits bullet on
refusal behaviour already exists from Plan 4 Stage D; add the
decomposition mitigation beside it, and the `tasks`-stays-empty limit
from Plan 5 Stage D); `docs/COMPACTION-DESIGN.md` section 14 (14.5
references D80 already; confirm nothing else in section 14 states the
overflow-advisory gap as still open, since it is now closed); `CLAUDE.md`
open-questions list (amend the entries nearest "tokenSamples" and the
escalation-rate question with a pointer to D80 and the Plan 5 Stage D
finding; do not delete the entries outright unless the question is fully
closed); `docs/DECISIONS.md` D78 through D80; `docs/FINDINGS.md`, "Plan 5
Stage D" section (just added, this session); `docs/PLAN-5.md` itself,
Stages A through D already marked done.

## Verified facts

Harness green at 31 of 31 checks as of commit `af4e748` (this session,
after Stage D). `docs/PLAN-5.md`'s Stage D section and exit criteria are
filled in and checked off. No further live `claude -p` runs are needed
for Stage E; do not start any.

## Work completed

Stage D closed this session: `docs/FINDINGS.md`'s "Plan 5 Stage D"
section and `docs/PLAN-5.md`'s Stage D tasks/exit-criteria, committed at
`af4e748`. Stages A through C were already done before this session
started (commits `f5787de` and earlier, per `docs/PLAN-5.md`'s own
history).

## Unresolved questions

Whether `CLAUDE.md`'s open-questions list should mark the `tokenSamples`
question closed-as-unobservable or leave it open pending a mechanism
other than duration or panel visibility (a third session on a different
platform version, say). Lean toward recording it as "duration is ruled
out; the mechanism is otherwise unknown" rather than closing it outright,
consistent with how the escalation-rate question above it is already
phrased as narrowed-not-answered. Whether `docs/COST.md`'s existing table
structure has a natural row for a per-arm comparison or needs a new
subsection; look at the file before deciding.

## Exact next action

Read `docs/COST.md` in full, then add the decomposition cost comparison
using the D80 figures above.

## Model and effort to set

`/model` sonnet, effort medium.

## Cost projection

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
