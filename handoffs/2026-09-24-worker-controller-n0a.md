# Handoff: worker-controller-n0a

Historical entry: N0A subsequently completed for operator review. Read the
[stage result](../docs/stage-results/worker-n0a.md) and use the
[N1 v2 handoff](2026-09-24-worker-routing-n1-v2.md) for the next stage.
The original pre-stage snapshot below is preserved.

<!-- handoff.py new --slug worker-controller-n0a --reason model-change --to-model gpt-6-astra --to-effort high --project . -->
Written 2026-09-24 by the planning session. Reason: future operator model-change.
Prepared only; no stage or model switch has started.

## Goal

Execute N0A only when the operator directs. Amend the worker execution contract
to remove the dependency-review blockers before N1, then stop for review.

## Decisions already made

Worker remediation precedes Controller remediation. Preserve B0, historical
evidence and existing Controller behaviour. N0A is design and offline validation,
not executor implementation. Separate task/attempt state, identity/overrides,
root accounting and optional Controller integration. No paid Claude calls or
subagents. No requirement to promote a new worker policy before X0.

## Files and links that matter

- Root: `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`.
- [Sequencing plan](../docs/WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md), section 5.
- [Execution contract](../docs/WORKER-EXECUTION-CONTRACT.md).
- [N0 record](../docs/stage-results/worker-n0.md).
- [Worker plan](../docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md).
- [Controller plan](../docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md).
- [Protocol](../docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `tools/route.py`, `tools/dispatch_budget.py`, `tools/acceptance.py`,
  `tools/model_registry.py`, `tools/evaluation_live_worker.py`,
  `tools/build_dist.py`, `tools/controller_dispatch.py`,
  `tools/controller_policy.py`, `tools/controller_evaluation.py`,
  `test/harness/controller_evaluation_r5_tests.py`.

## Verified facts

Planning HEAD `a70e311`; worktree initially clean. Graft semantic and wiring
freshness passed. The preceding dependency review passed the full offline
harness. The contract has no specified B0 next-attempt transition; this is a
design finding. Controller manifests bind shared registry files and reject
changes; existing fake tests execute those manifests. The evaluation worker
imports harness code. These source findings do not establish a runtime defect
in the new executor, which has not been implemented.
Planning-delivery checks also passed: this handoff's validator, local links,
cost arithmetic and the full offline harness on repeat with child-process
permissions after a sandbox permission error. See the plan's validation note.

## Work completed

The sequencing plan, current entry pointers and this handoff are prepared as
uncommitted documentation. N0A has not run. No runtime, source or bundle changed.
No provider experiment was run. Recheck HEAD and worktree on entry.

## Unresolved questions

N0A must freeze legal state transitions, revision/override semantics, recovery
and budget carry-forward, legacy record projections, adapter packaging, scoped
Graft capability and the historical/current test split. The proposed fixes are
not accepted implementation contracts yet. Host enforcement and live worker
quality remain unqualified. Define the statistical estimand and defer power
simulation to N4/N5; do not assume a universal minimum sample size.

## Exact next action

After operator start, read project instructions, verify branch/HEAD/worktree,
check your own Graft MCP access and call `graft_check_freshness`. Use scoped
Graft queries for the section 9 source anchors; do not silently substitute a
filesystem scan. Complete N0A sections A-D, version the contract amendment,
run the existing offline harness and write `docs/stage-results/worker-n0a.md`.
Prepare and validate a fresh N1 handoff with actual decisions, then stop.

## Model and effort to set

Operator selects **GPT-6 Astra / High** in the host before starting N0A.
Verify the receiving setting; this file does not switch the current session.
No switch is needed if already set. N1 subsequently uses GPT-5.6 Sol / High.

## Cost projection

Development API-equivalent estimate: **USD 3-20**, not a subscription bill.
Basis checked 2026-09-24: [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)
and [pricing](https://developers.openai.com/api/docs/pricing). Assume ordinary
input .10-.30M, cache reads .20-.80M, cache writes .02-.06M and output including
reasoning .02-.06M. Standard USD/MTok rates are 10/1/12.50/50 respectively.
Include 30 percent contingency and the protocol's Standard/Fast envelope.
Input categories are mutually exclusive; cache hits are assumed, not measured.
Reprice changed terms, long context and separately billed tools on entry.
Paid Claude experiment subtotal: **USD 0 planned**. Graft charges retain
standing approval but are unknown and excluded, not assumed free.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**2-4 hours** elapsed engineering/checking, excluding operator delays.
Re-estimate if the baseline or required amendment changes materially.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
