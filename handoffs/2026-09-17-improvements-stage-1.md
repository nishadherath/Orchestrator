# Handoff: improvements-stage-1

<!-- handoff.py new --slug improvements-stage-1 --reason model-change --to-model gpt-5.6-sol --to-effort high -->
Prepared 2026-09-17 for an operator-started session using the recommended
model/effort. No model change or new session has been performed.

## Goal

Implement Stages 0 and 1 of the improvements action plan: reproduce the audit
defects, establish the versioned attempt contract and make accounting/storage
safe. Preserve existing work. Real-world evaluation is deferred until last.

## Decisions already made

- Original improvement order is now 1, 2, 3, 5, 6, 4. The action plan splits
  accounting from learning; follow its stage dependencies.
- Use offline tests/fake runners for this work unit. No paid benchmark or
  Controller calls, routing-policy tuning or new real-world fixtures.
- Unknown cost is not zero; direct-start and escalation populations differ;
  task totals cannot be divided equally across workers.
- Use Graft MCP for every task. Check freshness and access before discovery;
  scoped file APIs and call tracing should guide the storage change. Each
  future child/resumed session needs its own correct checkout binding.
- Do not delegate by default. A new session/model/effort/agent requires a
  checked handoff and a cost/time notice under AGENTS.md.

## Files and links that matter

- `docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md`, Stage 0 and Stage 1.
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`.
- `docs/ASSESSMENT-2026-09-17.md`, findings R1-R9 and offline reproductions.
- `tools/route.py`: `load_ledger`, `append_ledger_entry`,
  `complete_ledger_entry`, `next_ledger_id`, `ledger_cell_means`, `posterior`, `plan`.
- `tools/claudep.py`, `tools/system_controller.py`, `tools/handoff.py`.
- `src/System/schemas/RoutingLedgerEntry.schema.json`, `test/harness/check.py`.
- `docs/REAL-WORLD-EVALUATION-PLAN.md`: deferred, not the current work queue.

## Verified facts

Graft MCP freshness reported both graphs in sync and file APIs returned the
route, Controller and handoff interfaces. `git status --short` showed extensive
pre-existing uncommitted source, generated bundle, documentation and local
configuration work. The last reviewed HEAD is `4fb4682` on `v1.0-beta`;
recheck it. `test/harness/check.py --json` returned 33 passes, zero failures
and skips after the planning changes, including all nine handoffs. The direct
handoff check passed too. Those checks do not close the audit defects; rerun
for the next baseline.

The handoff generator accepts arbitrary target-model text; its `/model`
wording is Claude-oriented. Use the Codex model selector for this handoff.

## Work completed

The audit, summary, Graft setup, standing handoff policy, real-world evaluation
proposal and ordered action plan have been written. The root charter points
to the new roadmap. Runtime audit repairs remain pending. No commit was made
for this planning handoff; do not treat the dirty worktree as disposable.

## Unresolved questions

Confirm the smallest sound transactional storage implementation. The plan
recommends standard-library SQLite with compatible JSONL import/export; inspect
current readers and migration boundaries before finalising that decision.
Parent/child billing inclusion and some cancellation behaviour require explicit
evidence; do not assume exact live cost attribution from a mocked test.
Actual served model/effort may be absent in older records and must stay unknown.

The default `python3` launcher previously failed under the sandbox. A working
Python is `C:/Users/Bob/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
Git may require a process-scoped safe.directory exception for this checkout.
Some Bash graders need that Python exposed as `python3`; the prior temporary
shim is under `$env:TEMP/orchestrator-audit-bin`, with `bash-env` for BASH_ENV.
Verify its existence and paths before reuse; do not modify global user settings
to work around a sandbox-only problem.

## Exact next action

In `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`, read the instructions and
Stage 0/1, call `graft_check_freshness`, inspect current changes and run the
offline harness. Add desired-behaviour regressions for pending cost records and
unequal per-attempt costs; use Graft to trace ledger writers. Define the shared
attempt/storage contract, then implement migration/accounting and their tests.
Keep the next patch bounded; do not begin Stage 7. Update the roadmap with
evidence and prepare the next handoff only when a transition is needed.

## Model and effort to set

Select **GPT-5.6 Sol (`gpt-5.6-sol`), high reasoning**, in the Codex model
selector, then start a fresh task in this same project and pass this file.
The host exposes this combination. This is a recommendation, not a setting
changed by the previous session. No child agents are scheduled.

## Cost projection

Stage 0 and the first Stage 1 work unit: **USD 2-8 direct API-equivalent**,
not a known subscription charge. Assumptions and arithmetic are recorded in
the action plan: 100k-400k ordinary input, 50k-200k cache writes, 300k-1,200k
cache reads and 30k-120k output including billed reasoning, plus 30 percent
contingency. Categories are disjoint. Standard rates from the
[official model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
checked 2026-09-17, give USD 1.37-5.48 before contingency. Keep requests below
the long-input surcharge threshold and reprice actual service/tool charges.
No paid Claude experiments are projected. The computed line below is a
historical load estimate, not a measurement of this Codex session or its bill.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Allow **4-8 hours** for the first sequential implementation session, including
investigation, changes and tests. Completing all pre-evaluation stages is a
separate 5-10 engineer-day planning range. If the first session cannot complete
Stage 1, retain a tested coherent increment and name the exact remaining work.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
