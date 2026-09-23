# Handoff: improvements-stage-2

<!-- handoff.py new --slug improvements-stage-2 --reason model-change --to-model gpt-6-astra --to-effort high -->
Prepared 2026-09-17 for an operator-started session using the recommended
model/effort. No model change or new session has been performed.

## Goal

Implement Stage 3 of `docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md`: enforce
Controller spending limits across concurrent calls with durable reservations,
complete failure accounting and idempotent recovery. Keep real-world evaluation
deferred until Stage 7.

## Decisions already made

- Stages 0-2 are complete. Keep version-2 task/attempt JSONL, direct and
  conditional capability populations, exact identity cohorts and selected-path
  projections intact.
- The Stage 3 invariant is authoritative spent plus outstanding reservations
  never exceeding the configured scope. Reserve before dispatch and reconcile
  every exit path. Ambiguous usage remains reserved.
- Use standard-library, process-safe persistence and reversible migration. Do
  not add an external runtime dependency, tune routing priors or run paid
  Claude experiments for the deterministic implementation gate.
- Use Graft for every task. Check freshness before discovery, query the current
  checkout, and refresh semantic summaries after source changes. The operator
  has standing project authorization for changed-source summaries through the
  configured DeepSeek endpoint; never print or store the key in the repository.
- Preserve the extensive existing dirty worktree. Do not reset, clean, commit
  or overwrite unrelated work.

## Files and links that matter

- `docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md`, Stage 3 and mandatory cases.
- `tools/system_controller.py`: `LiveRoleRunner`, `run_quick`, `BudgetExhausted`
  and all role/classifier dispatch paths.
- `tools/claudep.py`: `call_claude`, `ClaudeCallError.partial` and provider cap.
- `src/System/schemas/BudgetEntry.schema.json` and
  `src/System/schemas/RoutingLedgerEntry.schema.json`.
- `tools/route.py`, `tools/handoff.py`, `test/harness/improvement_regressions.py`.
- `docs/ATTEMPT-LEDGER-DESIGN.md`, D84 and D85 in `docs/DECISIONS.md`.
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`.

## Verified facts

HEAD is `4fb4682` on `v1.0-beta`; the worktree contains substantial authorized,
uncommitted work from the audit and Stages 0-2. The rebuilt redistributable is
stamped `2026-09-17-4fb4682-dirty`.

The full offline harness passes 35/35. `route.py --selftest` passes 23
scenarios, `claudep.py --selftest` passes four, audit regressions report
R1/R2/R5 PASS and only R3 XFAIL, routing replay is 125/125 after policy
exclusions, and ledger backtest is 29/29. Results are recorded in
`test/results/2026-09-17-harness.md`.

Graft deep refresh completed after the final source edit: 764 wiring nodes, 17
semantic summaries computed, 747 cached, zero stale and zero pending. `graft
check` reports both the context and wiring graphs in sync. Graft located
`LiveRoleRunner.__call__` at `tools/system_controller.py:362`: it checks a USD
0.50 floor but passes the fixed USD 2.00 `ROLE_CALL_CAP_USD`, so USD 0.60
remaining can authorize a USD 2.00 call. `classify` already uses
`min(0.10, remaining)`, but catches every exception and has no durable
reservation. The CLI creates one runner from a remaining-budget callback.

## Work completed

Stage 2 now separates direct-start and conditional escalation posteriors.
Version-2 capability learning requires acceptance pass/fail; terminal costs
retain failed, cancelled, interrupted and outer-unresolved spending. Automatic
learning uses exact model/bundle/policy/acceptance cohorts, with explicit cohort,
age and incompatible-pooling controls plus diagnostics. Projections start at
the selected worker and expose unpriced Controller failure/retry and
verification terms. No prior, threshold or routing row changed.

The schema now records `acceptance.contract_version`; cost provenance declares
that Controller failed runs are excluded and retry/verification costs are
unknown. Source docs, D85, tests, fixture and `dist/` are synchronized. Graft
authorization and credential location are accurately documented in
`docs/GRAFT.md`; the key remains in the Windows user environment.

## Unresolved questions

Choose the smallest durable reservation representation that works across
processes and restarts while keeping current JSONL artefacts readable. Specify
run-budget versus project-budget scope before code changes. Define when an
invocation becomes safely refundable, especially after timeout, cancellation
or a lost provider reply. Provider `--max-budget-usd` is a dispatch backstop,
not proof of invoice-level enforcement.

Decide how reservations relate to `BudgetEntry` records without introducing a
second ambiguous cost owner. Partial telemetry from `ClaudeCallError.partial`
must survive and reconcile, while unknown usage must remain reserved. The
implementation must cover concurrent generator calls rather than only the
sequential role runner.

## Exact next action

In `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`, read the project
instructions and this handoff, run `graft check .`, then use Graft to trace
`LiveRoleRunner`, `run_quick`, parallel generation and every `call_claude`
failure path. Turn the Stage 3 invariant into a small process-safe reservation
API and add the mandatory deterministic regressions before changing dispatch.
Make the existing R3 regression pass, add concurrency/interruption/restart
cases, rebuild `dist/`, run all 35 harness checks, refresh Graft and update the
action plan. Do not begin Stage 4 or Stage 7.

## Model and effort to set

Select **GPT-6 Astra (`gpt-6-astra`), high reasoning** in the Codex model
selector and start a fresh task in this project with this handoff. Stage 3
combines concurrent transactions, crash recovery and provider accounting; the
extra reasoning margin is justified for this correctness boundary. Do not
spawn agents unless the operator explicitly requests them.

## Cost projection

Stage 3: **USD 10-35 direct OpenAI API equivalent** at Standard GPT-6 Astra
rates, not a known Codex subscription charge. Assumptions: 0.3-1.0M uncached
input, 0.1-0.3M cache writes, 1-4M cached input and 60k-180k output/reasoning.
At USD 10/M input, USD 12.50/M cache writes, USD 1/M cached input and USD 50/M
output, this is USD 8.25-26.75 before a 25 percent contingency, rounded to the
range above. Keep individual prompts below the 272k long-input surcharge
threshold. Rates and threshold were checked 2026-09-17 on the
[official GPT-6 Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra).
One final Graft semantic refresh is expected; its DeepSeek charge is excluded
because this project does not receive token/billing usage from the adapter.
No paid Claude experiment is projected.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Allow **8-16 engineer-hours** for Stage 3 implementation, deterministic race
and interruption tests, documentation, bundle rebuild and full verification.
Split only at a tested transaction boundary if it exceeds one session.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
