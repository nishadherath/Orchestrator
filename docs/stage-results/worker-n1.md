# N1: durable worker execution and installable adapter

Date: 2026-09-24. Result: **offline implementation complete for review**.
The [v2 contract](../WORKER-EXECUTION-CONTRACT-v2.md) governs this stage.
N2 managed delegation and all experimental Controller integration remain pending.

## Delivered behaviour

- `tools/task_executor.py` admits one root task under a project writer registry,
  freezes its definition and acceptance, journals decisions and attempts,
  persists budget start and host intent before a call, and runs the qualified
  B0 sequence: Sonnet Low, one Sonnet Low repair, then Opus High. A verified
  pass stops the ladder; a verified quality failure alone advances it.
- Each attempt has its own receipt, cost, verification and output snapshot.
  The first failed output survives a later repair. Stale or conflicting
  receipts stay visible without authorising another call or task completion.
  Crash recovery joins decision, reservation, intent, receipt and settlement
  evidence, preserving unknown holds rather than assuming zero cost.
- `tools/dispatch_budget.py` retains one root balance across attempts and
  linked continuation revisions. Limit increases require a generation-fenced
  authority record. Cancellation and continuation preserve charges and holds.
  Its existing Controller-facing methods and v1 snapshot fields remain intact.
- `tools/worker_adapter.py` is a production-only import graph with an injectable
  transport. It requests an exact cell and effort, restricted built-in tools,
  and an explicit actor-scoped Graft-only MCP config. It omits `--safe-mode`
  because that flag disables MCP. Missing config, launcher or admission
  identity blocks command construction. Requested effort is recorded separately
  from unobserved served effort. Child-model or exact-identity violations block
  task acceptance.
- `tools/task_executor.py --audit --project .` is a read-only rollback gate.
  It returns nonzero for open tasks or unresolved holds. Consumer instructions
  preserve `.claude/task-executor-v2/` during rollback and prohibit a legacy
  relaunch until reconciliation.
- `tools/build_dist.py` now ships both production modules. The source README,
  lifecycle and consumer template explain the execution and rollback boundary.
  Historical Controller manifests were left byte-for-byte intact; separate
  current-code fake manifests exercise live runtime validation.

## Acceptance evidence

| Matrix IDs | Behavioural evidence |
| :--- | :--- |
| N1-01 to N1-04 | Exact B0 outcomes and call counts; complete state-edge enumeration; two-process admission race; stale callback reconciliation |
| N1-05 to N1-09 | Fault injection at reservation, start, intent, receipt and settlement boundaries; duplicate/conflicting receipts; missing cost and explicit reconciliation |
| N1-10 to N1-13 | Cancellation in each nonterminal state, deadline during an active writer, late receipt and linked continuation; rubric pass/fail/stale output; capability and verifier-only resume |
| N1-14 to N1-18 | Post-dispatch identity block, protected-file block, authorised partial closure, frozen input/definition/acceptance checks, stable revision through review and unsupported override |
| N1-19 to N1-25 | Writer-scope and authority conflicts, monotonic budget amendment, continuation without reset, child/effort rejection, allowlisted route-v2 projection, corruption rejection and rollback audit |
| N1-26 to N1-30 | Isolated copied-bundle import and fake task; old evaluation adapter checks; strict Graft command/config and missing-token/receipt mismatch negatives |
| N1-31 to N1-34 | Controller decision trap has zero calls on B0 failure; pinned historical and fresh fake manifests with mutation rejection; cancellation during verifier; inclusive charge counted once |

`python3 -m unittest test.harness.worker_executor_n1_tests
test.harness.worker_n1_manifest_tests -q` passed **40 tests**. The installed
consumer smoke test passed from a copied bundle without the original repository
or test tree. It verified admission, one fake host call, independent acceptance,
accounting, and the rollback audit before and after completion. The full
offline harness passed **57/57** with **71-file** distribution parity; its
machine-readable record is
[`test/results/2026-09-24-worker-n1-harness.json`](../../test/results/2026-09-24-worker-n1-harness.json).
No Claude worker or Controller provider call was made for N1.
The approved Graft deep semantic refresh completed; `graft_check_freshness`
reported both the semantic graph and wiring graph in sync with the code.

The REALWORLD harness initially exceeded its 120-second nested CLI timeout,
then its 300-second outer timeout on this Windows host. The two limits were
raised to 600 and 900 seconds respectively. The full corpus, per-task limits,
grader assertions and subprocess CLI check were retained. The final REALWORLD
check passed in 207 seconds and the full harness passed after the adjustment.

## Limits and next gate

These tests establish offline state, money and packaging behaviour with fake
worker transports. They do not prove that a live Claude process enforces
filesystem isolation, actually connects to actor-scoped Graft, or reports served
effort. The adapter validates the explicit config and launcher before dispatch;
a server that fails after launch is an infrastructure fault and cannot trigger
a B0 quality repair. An arbitrary interactive Agent-tool launch is unmanaged
because the current host offers no interception hook; a missing or mismatched
token cannot complete an executor task. Deadline timers act while the executor
process is alive and are rechecked on resume after a restart. N4 owns protected
oracle and Graft isolation proof; N2 owns child execution and budget envelopes.

The state-edge table is exhaustively enumerated in tests. Guard tests cover the
admission, owner, receipt, accounting, review, resume and cancellation classes;
they do not enumerate every possible combination of guards across all edges.
The journal and budget digests detect accidental or unsynchronised corruption,
not a malicious actor with write access who recomputes every digest. Both are
explicit residual risks, not evidence of a live-host qualification.

Stop after N1 for operator review. The next stage is N2, managed delegation,
using the same recommended GPT-5.6 Sol / High setting if the host has it.
