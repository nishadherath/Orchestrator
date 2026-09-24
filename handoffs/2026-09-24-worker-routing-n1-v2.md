# Handoff: worker-routing-n1-v2

<!-- handoff.py new --slug worker-routing-n1-v2 --reason model-change --to-model gpt-5.6-sol --to-effort high --project . -->
Written 2026-09-24 by the N0A session. Reason: future operator model-change.
Prepared for N1 after operator review; no switch or N1 execution has occurred.

## Goal

Implement N1 only against worker-execution-contract-v2. Deliver the durable
worker executor, installable adapter and all N1 acceptance evidence, then stop.

## Decisions already made

Use tools/task_executor.py and tools/worker_adapter.py. Reuse production budget,
acceptance, registry and route primitives. Separate task/attempt state and
immutable acceptance definition from evidence/review. One root budget survives
revision, override and continuation. B0 stays exact and Controller stays off.
Use sidecars plus allowlisted legacy projection. Preserve historical manifests;
current fake tests get separate temporary manifests. No paid Claude experiment,
unmanaged child launch or N2 implementation. Do not use the old v1 contract.

## Files and links that matter

- Root: `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`.
- [N0A result](../docs/stage-results/worker-n0a.md).
- [Contract v2](../docs/WORKER-EXECUTION-CONTRACT-v2.md).
- [34-case N1 matrix](../docs/WORKER-N1-ACCEPTANCE-v2.md).
- [Sequencing plan](../docs/WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md).
- [Worker plan](../docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md) and
  [protocol](../docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `tools/route.py`, `tools/acceptance.py`, `tools/dispatch_budget.py`,
  `tools/model_registry.py`, `tools/evaluation_live_worker.py`,
  `tools/build_dist.py`, `test/harness/controller_evaluation_r5_tests.py`.

## Verified facts

Baseline branch v1.0-rc1, HEAD a70e311, with the preceding planning changes
already uncommitted. Graft semantic and wiring freshness passed. Scoped source
retrieval confirmed mutable acceptance state, strict route-v2 attempt fields,
immutable existing budget limits, evaluation adapter harness imports and frozen
Controller manifest coupling. See N0A's validation evidence for final checks.
Final N0A checks: full harness 57/57, 17 valid handoffs, 69-file bundle parity,
15 legal design witnesses and byte-identical v1 archive. Design witnesses are
not execution tests; no production executor exists yet.

## Work completed

N0A preserved v1, wrote v2 and its acceptance matrix, corrected stage dependencies
and current pointers, and recorded evidence. Changes are uncommitted. No runtime,
consumer source, bundle or Controller algorithm was changed. No paid experiment
or subagent was launched. Read the final N0A record before implementing.

## Unresolved questions

N1 must prove all 34 matrix cases against real primitives/fake transports,
including budget amendment/continuation compatibility, admission crash windows,
legacy projection and installed-consumer imports. Graft isolation and host
enforcement remain unqualified; N1 exposes capability limits, N4 proves oracle
isolation. Served effort, model quality and statistical power are unmeasured.
No controller-specific repair is authorised by this worker stage.

## Exact next action

After operator direction, check branch/HEAD/worktree and preserve local work.
Read project instructions, verify your own Graft tool access and call
graft_check_freshness, then use scoped Graft retrieval for the named primitives.
Start with failing exact-B0, concurrent-admission and crash-window tests from
N1-01/N1-03/N1-05 through N1-07. Implement the smallest executor/adapter satisfying
the complete matrix. Run focused and full checks, build/verify the bundle and
fake installed consumer, record docs/stage-results/worker-n1.md, then stop.

## Model and effort to set

Operator selects **GPT-5.6 Sol / High** in the host. Confirm the receiving
setting; this document cannot switch or independently attest it. If already
set, no artificial switch is required. N2 keeps the same recommended settings.

## Cost projection

Development API-equivalent estimate: **USD 3.25-19.50**. Basis checked
2026-09-24: [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [pricing](https://developers.openai.com/api/docs/pricing), protocol unit I.
Assume ordinary input .25-.75M, cache reads .50-1.50M, cache writes .05-.15M
and output including reasoning .05-.15M. Standard USD/MTok rates are
4/.40/5/20 respectively; categories are mutually exclusive. The range includes
30 percent contingency and a Standard/Fast envelope. Cache hits are assumed,
not measured; reprice long contexts, changed terms, extra cycles and tool fees.
This is not a subscription bill. Claude experiment subtotal: **USD 0 planned**.
Separately authorised Graft refresh costs are unknown and excluded, not zero.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**5-9 hours** elapsed engineering and checks, excluding operator delays.
Re-estimate on a concrete implementation blocker; no paid-run time is included.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
