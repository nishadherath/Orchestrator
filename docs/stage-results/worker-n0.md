# Worker remediation N0: baseline and contract freeze

Date: 2026-09-21. Result: **complete for operator review; N1 not started**.

## Scope

N0 records the actual baseline and freezes the task/execution boundaries,
records, state transitions, host capability limits, B0 behaviour and future
evidence gates. It makes no runtime, source, bundle or Controller change and
makes no paid model call.

The implementation contract is
[`WORKER-EXECUTION-CONTRACT.md`](../WORKER-EXECUTION-CONTRACT.md). The programme
remains governed by
[`WORKER-ROUTING-ACTION-PLAN-2026-09-19.md`](../WORKER-ROUTING-ACTION-PLAN-2026-09-19.md)
and the [shared protocol](../REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).

## Baseline evidence

| Item | Observed value |
| :--- | :--- |
| Branch | `v1.0-rc1` |
| HEAD | `1798d6e80f193179dd6cf46879f0d033430ed1e8` (`Gap fixing plans`) |
| Initial worktree | Clean |
| Bundle stamp | `2026-09-18-1eb0fbe-dirty` |
| Graft | Semantic and wiring checks current on 2026-09-21 |
| Paid calls | None |

The bundle stamp predates HEAD because the intervening commit contains planning
documentation outside the redistributable source set. The offline distribution
parity check remains the authority on whether a rebuild is required.

The focused B0 reproduction ran:

```text
python -m unittest test.harness.qualified_default_tests -v
Ran 2 tests in 0.451s
OK
```

It verified all assessment combinations use policy B0 with the exact sequence
`worker-sonnet-low`, `worker-sonnet-low`, `worker-opus-high`, a three-attempt
ceiling, and no Controller.

The pre-edit full baseline ran `test/harness/check.py --json`: 57/57 checks
passed, all 69 distribution files matched the recorded bundle stamp, and all
14 existing handoffs validated. The final post-edit run also passed 57/57,
reported 409 authored files clean, retained 69-file bundle parity and validated
all 15 handoffs including the N1 transition handoff.

## Frozen decisions

1. N1 composes `route.py`, `acceptance.py`, `dispatch_budget.py`,
   `model_registry.py` and the restricted live-worker adapter behind one
   task-level executor. It does not create another registry or acceptance path.
2. Task identity binds goal, frozen acceptance and admitted input revision.
   Retry, repair, session restart and cell change remain within that revision.
3. The executor is the only task-state writer. It persists allowance and
   dispatch intent before side effects and fails closed on ambiguous recovery.
4. Acceptance remains independent. Worker prose and public checks alone cannot
   produce `accepted` or learning-eligible evidence.
5. N2 uses a deterministic bounded DAG with explicit file ownership and one
   parent budget. A model may propose a plan but cannot admit it.
6. Host capabilities are versioned evidence. Restricted CLI execution is
   programmatic; interactive Agent/Task control requires admission and receipt
   cooperation and cannot yet prevent arbitrary unmanaged launches.
7. Codex agents are development infrastructure and are not represented as
   equivalent to Claude consumer workers.
8. B0 remains unchanged and is the rollback path throughout N1-N7.
9. The 12-task N6 comparison is exploratory at the proposed 5-point safety
   margin. Best-case exact one-sided evidence requires at least 59 independent
   zero-regression tasks before multiplicity and quality-power adjustments.

## Gap ownership and expected evidence

| Gap in worker scope | Owning stage | Required closure evidence |
| :--- | :--- | :--- |
| Campaign terminal-stop semantics | N4 | Restart of every terminal state admits zero calls |
| Complete worker manifest | N4 | Mutation of every execution dependency invalidates admission |
| Genuine grading | N4 | Behavioural references pass; label-only and false-success variants fail |
| Fair assessment | N3-N4 | Production assessor sees public input only and writes no task answer |
| Worker cell selection | N3, N5-N7 | All cells explicitly resolve/reject; live candidate clears frozen gates |
| End-to-end execution | N1 | Durable dispatch, receipt, verification and recovery tests pass |
| Deterministic delegation | N2, N8 | DAG, ownership, nested-budget and host-boundary tests pass |
| Worker qualification | N5-N7 | Identity/cost screen plus independent development/reserved evidence |
| Worker documentation claims | Every stage, N8 | Claims cite the exact qualifying evidence and its limits |

Controller-specific gaps remain assigned to the deferred X programme. No N
stage may call a safer worker component a fix for an untouched Controller path.

## N1 executable acceptance matrix

N1 is complete only when focused tests demonstrate:

- all ten task states and every permitted/forbidden transition;
- one owner under concurrent admission and no duplicate host call;
- exact B0 order, stop-on-acceptance and three-attempt ceiling;
- no repair after permission, infrastructure, identity or accounting failure;
- crash before dispatch produces no call, crash after intent produces
  `uncertain`, and a committed receipt replays locally once;
- timeout and missing usage keep an allowance held until reconciliation;
- duplicate identical receipt is idempotent and conflicting receipt fails;
- required outputs and protected paths are independently checked;
- identity mismatch cannot pass, train or silently substitute a cell;
- cancellation blocks new dispatch and preserves in-flight accounting;
- existing version-2 ledgers remain readable and rollback preserves evidence.

Run focused tests, then the complete offline harness. Source changes destined
for consumers must use the supported bundle builder before delivery.

## Model and host observation

The plan recommends GPT-5.6 Sol at High for N0-N6. This development host exposed
the session only as GPT-5 and provided no independently verifiable effort value.
The session therefore does not claim the planned model identity or effort.
This limitation does not affect the provider-free baseline and contract output,
but it must remain visible in the stage record.

## Cost and time

Paid Claude experiment spend was **USD 0**. No provider call was made. The
development session's actual token categories and invoice are unavailable, so
actual API-equivalent cost is unknown rather than zero. The N0 planning envelope
was USD 1.25-6.50 and 2-3 hours; no measured billing claim is made here. Graft
reported retrieval reductions are estimates, not invoice savings.

## Unresolved work

N1 must choose the final module/package location after tracing concrete callers,
write the schemas and state owner, and implement the focused matrix above. N4/N5
must estimate paired-quality variance before deciding whether to enlarge N6 or
retain it as exploratory. Live model availability, served effort, quality and
cost remain unqualified.

Exact next action after operator approval: continue on GPT-5.6 Sol High if the
host exposes it, prepare a checked N1 continuation handoff only if a new session
or model/effort change is needed, and implement N1 against the frozen contract.
Stop after N1 for review.
