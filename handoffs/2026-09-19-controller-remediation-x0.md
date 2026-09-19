# Handoff: controller-remediation-x0

<!-- handoff.py new --slug controller-remediation-x0 --reason model-change --to-model gpt-6-astra --to-effort high --project . -->
Written 2026-09-19 by the planning session. Reason: future operator model-change.
Deferred handoff only; no model change or stage execution has occurred.

## Goal

When explicitly requested later, execute X0 of the deferred experimental
Controller remediation plan. Revalidate the defects and settle integration
contracts against the then-current worker implementation. Stop before X1.

## Decisions already made

Worker remediation executes first. Controller work is separately deferred;
this file is not permission to start. Reuse its verified executor and routing
contracts, but do not assume a candidate was promoted. Keep B0 as the qualified
default until later evidence and an operator decision justify changing it.
No paid Claude runs, implementation fixes or subagents in X0.

## Files and links that matter

- Root: `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`.
- [Deferred plan](../docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md), X0.
- [Worker plan](../docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md) and its later stage results.
- [Protocol and costs](../docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `tools/controller_matrix_runtime.py`, `tools/controller_pilot_runtime.py`,
  `tools/controller_corpus.py`, `tools/system_controller.py`,
  `tools/controller_dispatch.py`, `test/harness/check.py`.

## Verified facts

Planning baseline was `v1.0-rc1`, HEAD `1983834`. Graft semantic/wiring checks
passed. The preceding review reported 57/57 offline checks despite reproducible
terminal matrix restart and public-label grading defects. The first-entry
Generator mapping was source-confirmed. Task-wide Controller admission remains
a risk needing a concurrency reproduction, not a measured double dispatch.

## Work completed

The two remediation plans, shared protocol and initial handoffs were prepared
on 2026-09-19 as uncommitted documentation. No X stage has started. At actual
entry, replace this snapshot with the intervening worker results and commits.

## Unresolved questions

Whether intervening changes affect each defect; the worker programme outcome;
supported host integration; Generator assignment and count ownership contracts;
the final corpus and predeclared quality/cost gates. Existing R5 fixtures prove
plumbing only. No current live Controller uplift or all-cell quality claim.

## Exact next action

Only after operator start, verify branch/HEAD/worktree and read worker stage
results. Check your own Graft MCP access, call `graft_check_freshness`, and use
scoped retrieval before code discovery. Follow X0 to reproduce or reclassify
the six named findings without provider calls. Record contracts and evidence
in `docs/stage-results/controller-x0.md`. Stop and prepare a checked X1 handoff
for Sol High; do not launch X1 automatically.

## Model and effort to set

Operator selects **GPT-6 Astra**, **High** in the host when starting X0 later.
Verify availability then. This recommendation does not switch the current
session. X1 is planned for GPT-5.6 Sol High after review and a checked handoff.

## Cost projection

Development API-equivalent estimate: **USD 3-20**, not a subscription bill.
Basis checked 2026-09-19: [official Astra pricing](https://developers.openai.com/api/docs/models/gpt-6-astra)
and [API pricing](https://developers.openai.com/api/docs/pricing). Assume ordinary
input .10-.30M, cache reads .20-.80M, cache writes .02-.06M, output including
reasoning .02-.06M. Standard rates per million are 10/1/12.50/50 respectively;
include 30 percent contingency and a Standard/Fast envelope (Fast is twice
Standard). See protocol unit R. Cache hits are assumptions, not measurements;
reprice at the actual deferred start, including changed terms or long context.
Paid Claude experiment subtotal: **USD 0 planned**. Graft refresh charges are
separately authorised but unknown and excluded, not assumed free.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**2-4 hours** elapsed review/checking time, excluding operator delays. Re-estimate
if the implementation or defect scope has changed before this deferred stage.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
