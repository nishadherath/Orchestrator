# Handoff: worker-routing-n1

<!-- handoff.py new --slug worker-routing-n1 --reason model-change --to-model gpt-5.6-sol --to-effort high --project . -->
Written 2026-09-21 by the N0 execution session. Reason: future operator
model-change after N0 review. N1 has not started.

## Goal

Implement Stage N1 only: the durable task-level worker executor and host adapter
defined by `worker-execution-contract-v1`. Prove its state, dispatch, accounting,
acceptance and recovery behaviour offline, then stop for operator review.

## Decisions already made

Use the N0 contract as the reviewed boundary. Compose existing routing,
acceptance, budget, registry and adapter primitives behind one state owner.
Preserve exact B0, keep Controller disabled, retain current ledgers, fail closed
on ambiguity and make no paid Claude calls. Do not begin N2.

## Files and links that matter

- Root: `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`.
- [N0 result](../docs/stage-results/worker-n0.md).
- [Frozen execution contract](../docs/WORKER-EXECUTION-CONTRACT.md).
- [Worker plan](../docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md), N1.
- [Execution protocol](../docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `tools/route.py`, `tools/acceptance.py`, `tools/dispatch_budget.py`,
  `tools/model_registry.py`, `tools/evaluation_live_worker.py`,
  `tools/evaluation_live_episode.py`, `test/harness/check.py`.

## Verified facts

Baseline: branch `v1.0-rc1`, HEAD `1798d6e`, initially clean. Graft semantic
and wiring indexes were current. `python -m unittest
test.harness.qualified_default_tests -v` passed 2/2 and reproduced the exact
B0 sequence. The pre-edit full baseline passed 57/57, including 69 bundle files
at stamp `2026-09-18-1eb0fbe-dirty`. Read the N0 record for final validation.

## Work completed

N0 added the versioned execution contract and stage record, updated programme
status pointers and prepared this handoff. These N0 changes are uncommitted.
No runtime, source, bundle or Controller file changed. No provider call ran.

## Unresolved questions

The executor module does not exist. Trace concrete callers before choosing its
final location. Interactive Agent/Task launches cannot yet be atomically
intercepted and need an honest admission/receipt boundary. Model availability,
served effort, quality and cost remain unqualified. N6 is exploratory unless
its independent task sample is enlarged after N4/N5 power analysis.

## Exact next action

After operator approval, verify branch, HEAD and worktree; read the N0 record
and contract. Check your own Graft access with `graft_check_freshness`, then
trace callers of the five reused primitives before broad reads. Write focused
failing tests for concurrent admission, pre/post-dispatch crashes and exact B0
first. Implement the smallest task owner that passes the complete N1 acceptance
matrix. Run focused checks, build `dist/` only if shipped source changes, run
the full harness, record `docs/stage-results/worker-n1.md`, and stop before N2.

## Model and effort to set

Operator selects **GPT-5.6 Sol**, **High** in the host after accepting N0.
Official documentation confirms High is supported. Verify the host selection;
this handoff does not perform it. Do not substitute another model silently.

## Cost projection

Development API-equivalent estimate: **USD 3.25-19.50**, not a subscription
bill. Official [GPT-5.6 Sol documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [API pricing](https://developers.openai.com/api/docs/pricing) checked
2026-09-21 list short-context Standard rates per million tokens of USD 4 input,
0.40 cached input, 5 cache writes and 20 output; output includes reasoning.
Assume .25-.75M ordinary input, .50-1.50M cache reads, .05-.15M cache writes
and .05-.15M output, with mutually exclusive input categories and 30 percent
contingency. That is USD 3.25-9.75 Standard; the upper envelope allows the
documented Fast tier at twice Standard. Long-context requests above 272K input,
regional charges, separately billed tools or changed rates require repricing.
Cache hits are assumptions, not measured savings.

Paid Claude experiment subtotal: **USD 0 planned**. N1 uses fake adapters and
local subprocess fixtures only. Graft remains separately authorised; any
refresh charge is unknown and excluded rather than treated as zero.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**5-9 hours** elapsed engineering and checking time, excluding operator delay.
Stop and re-estimate if the frozen boundary or host capability changes.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
