# Handoff: plan6-stageD

<!-- handoff.py new --slug plan6-stageD --reason effort-change --from-model sonnet --from-effort medium --to-model sonnet --to-effort high --project . -->
Written 2026-09-16 by sonnet, medium. Reason: effort-change.

## Goal

Execute `docs/PLAN-6.md` Stage D: harness, tools and artefact fixes from
`docs/AUDIT-2026-09-16.md`, tasks D.1 to D.5 in that order, each its own
commit naming the audit findings it closes. This is the plan's last
stage. Zero live spend.

## Decisions already made

D81 (Stage A) still governs A4, B1 and A22; D.1 executes A22's
two-stage-default and `resolve_two_axis`-retirement halves, already
decided, not reopened. No new decision is expected from D.1 to D.4,
which are mechanical fixes to the audit's own Fix sentences. D.5 writes
the plan's own close-out decision entry, next number **D83**, not D82:
D82 was already used in Stage C.4 for two erratum notes (B11, B16)
found while executing that stage, so the plan text's own reference to
"D82" for the close-out entry is now off by one and D.5 should write
D83 instead.

## Files and links that matter

`docs/PLAN-6.md` Stage D (D.1-D.5); `docs/AUDIT-2026-09-16.md` pass 1
(A1, A2, A3, A9, A11, A21, A22, A23, A24, A25, A34) and pass 3 (C3, C5,
C7, C9); `tools/route.py`'s `resolve_two_axis` and its CLI path;
`test/harness/score_routing.py`, `build_dist.py`, `check.py`
(`PROSE_GLOBS`, INV7, DIST); `test/harness/results_index.py` (new);
`test/harness/fixture_fingerprint`, `role_probe.py`,
`cost_rollup_check.py`, `extract_e30.py`, `compaction_bench.py`,
`tools/generate_priors.py`; `dist-rubric-only/` and its `.gitignore`
line.

## Verified facts

`python3 test/harness/check.py`: 0 failing of 32 at `1197081`, the
commit that closes Stage C plus a cherry-picked fix
(`9436ade`/`task_b5e22575`, spawned during Stage C, for stale
`context-usage.json` references after the A12 file split; unrelated to
any Plan 6 task but merged onto `v1.0-beta` before Stage D started).
`dist/` last rebuilt and stamped clean at `b55d618`; Stage C touched no
shipped file, so `dist/` is not yet rebuilt against the cherry-picked
fix or any of Stage C's commits (README.md and docs/ are not shipped).

## Work completed

Stage A: `2b1902f`ff, `docs/PLAN-6.md`, D81, the Stage B handoff. Stage
B: `2280efe` through `8827017`, all ten B.1-B.10 tasks. Stage C:
`fb0b54e` through `c353f4c`, all five C.1-C.5 tasks, plus `1197081`
(the cherry-picked out-of-plan fix). All checkboxes and status lines
through Stage C are checked/done.

## Unresolved questions

Whether D.1's `resolve_two_axis` deletion needs `score_routing.py`'s
`--axes 2` CLI option removed in the same commit or a follow-up; the
plan's own B.8 amendment says "together", read it before splitting.
Whether D.3's `results_index.py` needs to run once manually before
wiring it into `check.py --record`, to catch a first-run defect before
it is load-bearing.

## Exact next action

Read `docs/PLAN-6.md` Stage D, then `docs/AUDIT-2026-09-16.md` findings
A22, A21, A9 and C3, then start task D.1: `score_routing.py` defaults to
`--classifier two-stage`.

## Model and effort to set

`/model` sonnet, effort high.

## Cost projection

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
