# Handoff: worker-routing-n0

<!-- handoff.py new --slug worker-routing-n0 --reason model-change --to-model gpt-5.6-sol --to-effort high --project . -->
Written 2026-09-19 by the planning session. Reason: future operator model-change.
Prepared only; no model change or stage execution has occurred.

## Goal

Execute N0 of the worker remediation plan only after the operator says to start.
Freeze the baseline, stage contracts and acceptance gates for worker selection,
execution and delegation. Experimental Controller fixes belong to the deferred
plan and are excluded.

## Decisions already made

Follow the common staged protocol. Stop after N0 for operator review. Preserve
B0 until qualified evidence and an explicit promotion decision exist. No paid
Claude calls or subagents in N0. Do not modify Controller runtime or resume R5.

## Files and links that matter

- Root: `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`.
- [Worker plan](../docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md), especially N0.
- [Protocol and costs](../docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
- [Deferred plan](../docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md).
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `tools/route.py`, `tools/controller_dispatch.py`, `tools/model_registry.py`,
  `tools/evaluation_live_worker.py`, `test/harness/check.py`.

## Verified facts

Planning baseline: `v1.0-rc1`, HEAD `1983834`, initially clean tracked worktree.
Graft semantic and wiring freshness passed. The preceding review recorded
57/57 offline checks and 69-file bundle parity. This does not close the gaps.
Recheck the checkout and actual host controls when execution starts.

## Work completed

Two staged plans and their shared protocol were written on 2026-09-19. The
planning changes are uncommitted. No remediation stage has started and no
runtime behaviour changed in this planning session.

## Unresolved questions

N0 must settle host execution/receipt boundaries, shared-module ownership,
task-state invariants and qualification gates before implementation. Proposed
module names are not existing APIs. Live cell qualification and improvements
in routing quality remain unproven.

## Exact next action

After operator start, verify branch, HEAD and worktree. Read project instructions
and check your own Graft MCP access; call `graft_check_freshness`, then scoped
Graft APIs before source discovery. Read N0, run its offline baseline, and
write `docs/stage-results/worker-n0.md` with the agreed contracts and evidence.
Finish N0 only; report results and stop before N1.

## Model and effort to set

Operator selects **GPT-5.6 Sol**, **High** in the host before starting N0.
Verify availability; do not substitute a Claude worker or claim a switch from
this document. No switch is needed if these settings are already active.

## Cost projection

Development API-equivalent estimate: **USD 1.25-6.50**, not a subscription bill.
Basis checked 2026-09-19: [official Sol pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [API pricing](https://developers.openai.com/api/docs/pricing). Assume ordinary
input .10-.25M, cache reads .20-.60M, cache writes .02-.05M, output including
reasoning .02-.05M. Standard rates per million are 4/.40/5/20 respectively;
include 30 percent contingency and a Standard/Fast envelope (Fast is twice
Standard). See protocol unit B. Cache hits are assumptions, not measurements;
reprice changed terms, long context or larger usage at execution.
Paid Claude experiment subtotal: **USD 0 planned**. Graft is separately
authorised; any refresh charge is unknown and excluded, not assumed free.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**2-3 hours** elapsed engineering/checking time, excluding operator delays.
Re-estimate after baseline discovery if scope or environment has changed.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
