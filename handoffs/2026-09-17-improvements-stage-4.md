# Handoff: improvements-stage-4

<!-- handoff.py new --slug improvements-stage-4 --reason model-change --to-model gpt-5.6-sol --to-effort high -->
Prepared 2026-09-17 for an operator-selected model change. No switch or new session has been performed.

## Goal

Implement Stage 4 of `docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md`:
acceptance evidence tied to the actual artefact, honest completion states and
actionable recovery. Keep real-world evaluation deferred to Stage 7.

## Decisions already made

Stages 0-3 are complete. Preserve version-2 task/attempt accounting, exact
learning cohorts, selected-path projections and durable per-run Controller
reservations. Claimed success alone must never qualify new learning evidence.
Keep measured spending regardless of success eligibility. No new routing
thresholds, empirical priors, consumer migration or paid Claude experiments.

Use Graft MCP for every task, session and agent. Start with freshness, then
scoped discovery. Standing project authorisation covers changed-source semantic
summaries through the configured DeepSeek endpoint. Credentials are in the
Windows user environment; never print them. Read `docs/GRAFT.md` for the local
adapter workaround. Do not spawn agents without an explicit request.

Preserve the existing dirty worktree. Do not reset, clean or commit it.
Explicit user constraints remain binding even when their rationale is false.

## Files and links that matter

- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`.
- `docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md`, Stage 4 tasks and gate.
- `tools/route.py`, `tools/system_controller.py`, `tools/dispatch_budget.py`.
- `src/System/schemas/RoutingLedgerEntry.schema.json` and schema README.
- `src/LIFECYCLE.md`, `src/ROUTING.md`, `src/SELF-LEARNING.md`.
- `test/harness/check.py`, `test/harness/dispatch_budget_tests.py`.
- `docs/ATTEMPT-LEDGER-DESIGN.md`, `docs/DISPATCH-BUDGET-DESIGN.md`, D84-D86.
- `test/results/2026-09-17-harness.md`.

## Verified facts

The recorded final Stage 3 harness passes 36/36, including 28 dispatch-budget
tests. Installed-bundle Controller selftest passes 12 scenarios. R1/R2/R3/R5
all pass; replay is 125/125 and backtest 29/29. The bundle stamp is
`2026-09-17-4fb4682-dirty`; changes remain uncommitted. Graft freshness was
checked again while preparing this handoff: both graphs are in sync.

Recovery regenerates accounting and reports without replaying provider calls;
automatic pipeline continuation is not implemented. Budget scope is per run.
Provider invoice enforcement and live output-setting enforcement are unverified.

## Work completed

Stage 3 added atomic reservations, retained failure/unknown charges,
idempotent reconciliation, cancellation, elapsed and output controls, and
preserved successful parallel output. Source instructions and dist are rebuilt.
The current action plan and CLAUDE.md identify Stage 4 as next. Stage 4 has not
started; no new commit was made for this handoff.

## Unresolved questions

Define the smallest acceptance contract and artefact identity that detects
edits after verification, including uncommitted and relevant untracked files.
Specify verifier provenance and protected-test identity without treating a
worker-supplied boolean, exit code or editable evidence file as independent proof.
Define rubric/human-review states for work without an executable oracle.
Inventory owned completion paths and document which external lifecycle events
remain unobservable when hooks or transcripts are missing.

## Exact next action

In `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`, read the project instructions
and this handoff, check Graft freshness, then trace routing completion,
acceptance eligibility and Controller/harness exits through Graft. Specify the
acceptance and evidence contract before editing schemas. Add the Stage 4 cases:
claimed pass with failing checks; absent/stale evidence; edited artefacts;
duplicate terminal events; crash before completion; blocked work; missing hooks;
and an attempt to weaken a protected test. Implement the smallest shared
boundary, diagnostics and consumer guidance. Rebuild dist through its gate,
run the complete harness, refresh Graft and record evidence. Do not start Stage 5.
Use Python -B for bundle smoke tests so bytecode does not fail the exact manifest.

## Model and effort to set

Select **GPT-5.6 Sol (`gpt-5.6-sol`), High** in Codex. Start a fresh project
session with this handoff to avoid carrying Stage 3's large history across the
switch. This is a cost-sensitive starting recommendation, not a measured
Stage 4 capability result. Escalate to Astra High only if a concrete provenance
or crash-recovery design problem remains unresolved; save a new handoff first.

## Cost projection

Estimate **USD 5-13 direct OpenAI API equivalent**, not a measured Codex bill.
Assume 0.3-0.8M uncached input, 0.1-0.25M cache writes, 1-3M cache reads and
50k-120k output/reasoning tokens. At USD 4/M input, 5/M cache writes, 0.40/M
cache reads and 20/M output, the base is USD 3.10-8.05; add 50 percent for
retries and uncertainty and round. Keep prompts below 272k input tokens.
Rates checked 2026-09-17 on the [official Sol model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol).
Cache reuse after a model switch is not assumed; these volumes are planning
assumptions, not telemetry. No paid Claude experiment is projected. Graft's
DeepSeek summary charge is additional and unknown because the current adapter
does not expose billed usage. No claim of measured Graft dollar savings.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Allow **2-4 hours elapsed agent implementation and verification**, with up to
6 hours if provenance or recovery requires a wider redesign. This is a rough
planning range, not a measured runtime or delivery promise.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
