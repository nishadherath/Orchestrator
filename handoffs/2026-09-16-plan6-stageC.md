# Handoff: plan6-stageC

<!-- handoff.py new --slug plan6-stageC --reason effort-change --from-model sonnet --from-effort high --to-model sonnet --to-effort medium --project . -->
Written 2026-09-16 by sonnet, high. Reason: effort-change.

## Goal

Execute `docs/PLAN-6.md` Stage C: prose fixes to the repository's own
documents (not the consumer bundle) from `docs/AUDIT-2026-09-16.md`,
tasks C.1 to C.5 in that order, each its own commit naming the audit
findings it closes. Zero live spend.

## Decisions already made

D81 (Stage A) still governs A4, B1 and A22; nothing in Stage C reopens
them. Stage C is pure prose against the audit's own Fix sentences; no
new decision is expected, but rule 4 still applies if one is needed
(e.g. if C.3's `docs/PREMISES.md` corrections turn out to require a
judgement call rather than a transcription).

## Files and links that matter

`docs/PLAN-6.md` Stage C (C.1-C.5); `docs/AUDIT-2026-09-16.md` pass 2
(B2-B5, B8-B13, B15-B17) and pass 3 (C2, C6); `CLAUDE.md`; `docs/COST.md`;
`docs/PREMISES.md`; `docs/FRONTIERS.md`; `test/fixtures/README.md`;
`test/fixtures/benchmark/README.md`; `src/routing_table.json`'s comment;
`docs/ROUTING-2-DESIGN.md`; `docs/CLASSIFIER-DESIGN.md`; `docs/PLAN.md`'s
cost summary; `docs/FINDINGS.md`; `docs/PLAN-4.md`; `test/harness/empirical-checklist.md`;
root `README.md`.

## Verified facts

`python3 test/harness/check.py`: 0 failing of 32 at `8827017`, the commit
that closes Stage B. `dist/` rebuilt and stamped clean at `b55d618`, the
last commit that touches shipped files; Stage C touches none of them, so
no rebuild is expected mid-stage. `orchestrator-scratch` reinstalled at
that bundle, `preflight.py` 0 failing of 18
(`test/results/2026-09-16-dogfood-install.md`).

## Work completed

Stage A: `2b1902f`ff, `docs/PLAN-6.md`, D81, the Stage B handoff. Stage B,
one commit per task: `2280efe` (B.4), `dea4c22` (B.5), `5f18ea2` (B.6),
`9c8bbd4` (B.7), `f023e2c` (B.8), `b55d618` (B.9), `8827017` (B.10, and
the earlier B.1-B.3 commits precede `2280efe` in the same run). All ten
B.1-B.10 checkboxes and Stage B's status line are checked/done as of
`8827017`.

## Unresolved questions

Whether C.3's `docs/PREMISES.md` "last checked" column needs a value for
every row or only the ones D44/D64/D80 touched; read the audit's B3-B5
Fix sentences before deciding, do not guess a format. Whether C.4's
`docs/PLAN-4.md` Stage B total correction (42.04) requires recomputing
from `test/results/` or simply transcribing the audit's own arithmetic;
check the audit finding's evidence first.

## Exact next action

Read `docs/PLAN-6.md` Stage C, then `docs/AUDIT-2026-09-16.md` findings
B9, C6, A2 and C2, then edit `CLAUDE.md`'s opening paragraph and Layout
section and the Working practice "Paid runs" paragraph (task C.1) as the
first commit.

## Model and effort to set

`/model` sonnet, effort medium.

## Cost projection

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
