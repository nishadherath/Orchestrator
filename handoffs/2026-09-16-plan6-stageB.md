# Handoff: plan6-stageB

<!-- handoff.py new --slug plan6-stageB --reason model-change --from-model fable --from-effort high --to-model sonnet --to-effort high --project . -->
Written 2026-09-16 by fable, high. Reason: model-change.

## Goal

Execute `docs/PLAN-6.md` Stage B: the consumer-bundle fixes from
`docs/AUDIT-2026-09-16.md`, tasks B.1 to B.10 in that order, each its own
commit naming the audit findings it closes. Zero live spend.

## Decisions already made

D81 fixed three answers: an unescalated floor failure counts in the
posterior (A4); `--spawn` ships in `ORCHESTRATOR.md` section 3 and the
record command becomes `--record --pending` (B1); two-stage becomes
`score_routing.py`'s default and the rubric-only suffix check goes (A22,
Stage D, not this stage). Rank order is not to be reshuffled; the
audit's Fix sentences are the specification for each task.

## Files and links that matter

`docs/PLAN-6.md` Stage B; `docs/AUDIT-2026-09-16.md` pass 1 (A-findings)
and pass 2 (B1, B6, B7, B14, B18, D1, D2); D81; `src/ROUTING.md`,
`src/LIFECYCLE.md`, `src/README.md`, `src/settings.fragment.json`,
`src/preflight.py`, `src/commands/workers.md`; `tools/route.py`,
`tools/context_probe.py`, `tools/system_controller.py`, `tools/claudep.py`,
`tools/handoff.py`, `tools/generate_workers.py`, `tools/build_dist.py`;
`test/harness/check.py` for the new ROUTE-MODES check.

## Verified facts

`python3 test/harness/check.py`: 0 failing of 31 at `ab7fa7a` and again
after `docs/PLAN-6.md` and D81 were written. `dist/` is byte-identical
to `build_dist.planned_files()` apart from the stamp (audit pass 1). A4
and A7 were reproduced in a scratch project (audit pass 2, last
section). No `claude -p` call was made in the audit session.

## Work completed

`2b1902f` the audit; `ab7fa7a` the root README and CLAUDE.md's Layout
line; Stage A of Plan 6 (this plan file, D81, this handoff) in the two
commits that follow it.

## Unresolved questions

Whether B.5's change to `posterior()` moves any bucket's `first` in
`backtest_ledger.py`; the plan says record it in D82, not revert.
Whether `context_probe.py`'s split into two files (B.8) needs the
fragment's commands to change; check before editing. Whether the
rationale-span approach or a URL is the right fix for the dead
citations in B.7; either satisfies A30.

## Exact next action

Read `docs/PLAN-6.md` Stage B, then `docs/AUDIT-2026-09-16.md` findings
C1, B6, B7 and D1, then delete `USAGE_PROJECT.md` and drop its README
row (task B.1) as the first commit.

## Model and effort to set

`/model` sonnet, effort high.

## Cost projection

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
