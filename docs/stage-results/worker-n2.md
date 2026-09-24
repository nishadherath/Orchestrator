# N2: managed delegation under one root

Date: 2026-09-24. Result: **offline implementation complete for operator review**.
Baseline commit: `fc67209` (N0A/N1). N3 has not started.
The [v2 execution contract](../WORKER-EXECUTION-CONTRACT-v2.md) and
[worker-first plan](../WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md)
govern this stage. The [consumer guide](../../src/MANAGED-DELEGATION.md)
defines the proposal and API.

## Delivered behaviour

- `tools/managed_delegation.py` admits an opt-in, static child graph only on an
  unused ready `TaskExecutor` root. Model proposals are untrusted. Validation
  freezes child acceptance and rejects cycles, missing links, unsafe paths,
  write/read races without an ordering dependency, unavailable cells, depth or
  concurrency beyond declared host capability, and budget oversubscription.
  An actual overlapping pair may run only after an explicit dependency orders
  it. Child work has one requested model/effort and one call, with no model-led
  recursive spawning.
- Every child call reserves once in the existing root `DispatchBudget`.
  Parent envelopes cap nested call totals and do not create a second charge.
  A root completion reserve remains available for the parent B0 worker. The
  root task and journal own child admission, intent, receipts, independent
  acceptance and final status. Only the root executor can cancel or accept the
  parent. A root pass rechecks all required child output and protected evidence.
- A runner lock excludes a second process while ready child waves execute.
  The root lock is released during adapter and verifier work. Cancellation
  signals active child invocations, settles calls proven unused at zero and
  preserves in-flight holds until a terminal receipt or explicit
  reconciliation. A persisted receipt is settled and verified on restart;
  an ambiguous started call is never automatically replayed. A failed or
  unqualified child blocks dependent work and parent completion.
- The production `WorkerAdapter` exposes its real boundary:
  `managed_delegation_enforced: false`. It cannot prove child filesystem
  isolation or intercept arbitrary interactive Agent launches, so N2
  admission rejects live managed delegation on that adapter. Fake hosts with
  declared enforcement exercise the whole orchestration path. No Controller
  invocation was added, and ordinary B0 remains the default.
- The checked builder ships `managed_delegation.py` and
  `MANAGED-DELEGATION.md`. Source lifecycle, consumer template and README
  explain admission, recovery and rollback. The isolated consumer test imports
  and runs this path from a copied bundle without the source tree.

## Acceptance evidence

The focused suite covers independent parallel calls, ordered nested work,
parent envelopes, graph rejection before launch, failed dependencies,
single-owner runner admission, pre-start and post-start crash windows,
persisted-receipt recovery, cancellation during an active call, late charge
reconciliation, unknown cost, identity and untracked-child-model faults,
rubric review, and parent rejection after accepted child output changes.
Tests use observable fake adapter calls and the real executor, budget,
acceptance and persistence modules. The existing N1 suite remains a regression
gate; the full offline harness and isolated distribution smoke test are run
separately. `python3 -m unittest test.harness.worker_delegation_n2_tests
test.harness.worker_executor_n1_tests test.harness.worker_n1_manifest_tests -q`
passed **58 tests**. `python3 tools/build_dist.py` passed its offline gate and
produced a **73-file** bundle. The copied-bundle consumer smoke test passed B0
and N2 fake tasks with no source-tree imports. The post-build full harness
passed **57/57**, zero skips; its [JSON record](../../test/results/2026-09-24-worker-n2-harness.json)
includes DIST parity, REALWORLD and RELEASE checks. At this pre-commit point,
RELEASE reported no mechanical failures and two operator actions: a clean
source stamp and publication. The source-stamped package build follows the
source commit. No paid Claude worker or Controller call was made for N2.

## Limits and next gate

The graph is admitted explicitly through the Python API; it does not intercept
interactive Task/Agent launches or change default routing. The production
adapter's restricted CLI and actor-scoped Graft configuration do not prove
filesystem or MCP index isolation. N4 must demonstrate those boundaries with
protected sentinel material before live managed child work can be enabled.
Host capability limits in fake tests are declared fixture values, not measured
live Claude limits. Served effort remains unobservable; requested effort is
recorded as a CLI argument. An ambiguous call can end as an incomplete task
after its cost is reconciled; no provider side effect is repeated to chase a
quality outcome. The parent B0 worker runs after accepted children, so an
explicit plan must budget for that final integration call.

Stop after N2 for operator review. N3, public-input assessment and experimental
worker selection, starts only on operator direction. The planned setting is
GPT-5.6 Sol / High if available on the receiving host; this session did not
independently verify its own model or effort setting.
