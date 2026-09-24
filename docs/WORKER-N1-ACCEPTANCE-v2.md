# N1 acceptance matrix for execution contract v2

Frozen by N0A, 2026-09-24. Status: **N1 offline tests run; see the
[stage result](stage-results/worker-n1.md) for evidence and limits**.
Authority: [contract v2](WORKER-EXECUTION-CONTRACT-v2.md).
N1 must implement these as behavioural tests against the executor and real
production primitives with fake transports. A document walk or legacy harness
pass is not evidence that the new executor meets them. Include positive and
negative cases, observable adapter call count, task identity and money balances.

## Task, attempt and recovery requirements

| ID | Setup/action | Required observable result |
| :--- | :--- | :--- |
| N1-01 | Success on first, second and third B0 attempts; fail all three | Exact policy cells/order; 1/2/3/3 calls; one revision; terminal accepted/accepted/accepted/failed |
| N1-02 | Try every allowed and forbidden lifecycle edge with valid/invalid guards | Only table edges with satisfied guards succeed; no terminal reopening |
| N1-03 | Two executor processes admit the same task concurrently | One owner generation and one host call; loser gets explicit conflict |
| N1-04 | Restart or callback with stale owner/decision generation | No new call or state overwrite; late receipt retained for reconciliation |
| N1-05 | Crash before reservation, after reservation, before budget start | Local recovery joins operation ids; no duplicate reservation; proven unused hold can settle zero |
| N1-06 | Crash after budget start but before host intent, or after intent before receipt | Uncertain task, retained allowance/writer barrier, zero calls on replay |
| N1-07 | Receipt committed, then crash before settle/verify/task transition | Local idempotent completion; no extra host call; one charge |
| N1-08 | Identical receipt twice; then conflicting receipt | Duplicate is idempotent; conflict blocks and preserves both evidence references |
| N1-09 | Timeout, missing cost, late cost or unknown process termination | Uncertain; no acceptance or next admission; proof and explicit resume needed |
| N1-10 | Cancel/deadline during every non-terminal state | Cancelled remains terminal; signal active writer, retain holds, no new admissions |
| N1-11 | Late receipt after cancellation; then authorised continuation | Original stays cancelled; settlement only; new revision allowed only after stopped writers and settled root, same charges |
| N1-12 | Pending rubric review followed by pass/fail/stale artefacts | Awaiting-review then verification on same attempt/revision; no worker call for review; stale evidence cannot pass |
| N1-13 | Pre-dispatch capability block; verifier-only block | Explicit resume after correction; only unused slot may admit a worker; verifier resume never launches one |
| N1-14 | Post-dispatch infrastructure/permission/identity failure | No B0 quality repair/fallback; explicit closure or proven receipt correction only |
| N1-15 | Ordinary quality failure versus protected-file tampering | Only ordinary failure can select next B0 slot; boundary violation blocks |
| N1-16 | Operator finalises useful incomplete work | Partial stays terminal and distinct from pass; root accounting is known |
| N1-17 | Mutate frozen goal, permissions, input or acceptance | Reject mismatched evidence; deliberate operator change requires linked revision |
| N1-18 | Change acceptance evidence/review; restart; propose cell override | Definition/revision digest stable; non-B0 dispatch override explicitly unsupported in N1 |
| N1-19 | New revision/root id, reused root authority or reconnect while prior writer/hold unresolved | Project writer registry rejects overlapping work; root-creation grant cannot be duplicated; no escape from root balance |
| N1-20 | Raise limit with authorised amendment; duplicate/conflicting authority; reopen with different limit | Monotonic authorised change only, charges/holds unchanged; duplicate idempotent, conflict rejected; ordinary reopen cannot amend |
| N1-21 | Cancelled root and unauthorised resume; authorised continuation with settled predecessor | Old generation cannot dispatch; new generation needs explicit authority, preserves root totals and old terminal task |
| N1-22 | Unknown identity, untracked child models, unavailable cell or effort evidence absent | No silent substitution; reject identity violations; keep requested effort distinct from served effort |
| N1-23 | Rich sidecar projected into legacy route-v2 | Existing validator accepts allowlisted fields/enums; repair represented as legacy escalation plus linked sidecar; unknown never trains |
| N1-24 | Corrupt journal, budget, acceptance, digest or migration input | Fail closed without deleting/resetting state; diagnostic identifies evidence needed |
| N1-25 | Roll back with unsettled tasks | Old data readable or explicitly rejected; pending work cannot relaunch through fallback instructions |

## Integration and packaging requirements

| ID | Setup/action | Required observable result |
| :--- | :--- | :--- |
| N1-26 | Import production executor/adapter in installed consumer without repository/test tree | Imports succeed with only bundled production dependencies |
| N1-27 | Run fake B0 task through installed consumer entry point | Admission, receipt, accounting and independent acceptance work; bundle parity passes |
| N1-28 | Existing evaluation adapter callers and command fixtures | Compatible entry points and identity/accounting checks remain; fixtures stay outside production imports |
| N1-29 | Strict tool/MCP configuration, scoped Graft unavailable | Managed path blocks with specific capability reason; no broad permission bypass or silent Graft omission |
| N1-30 | Interactive token missing, stale, consumed or receipt identities differ | No managed completion; unmatched launch remains unmanaged, with no host-interception claim |
| N1-31 | Instrument Controller adapters in every worker path | Zero Controller calls for success, repair, failure, uncertainty and cancellation |
| N1-32 | Historical manifest against frozen baseline; changed dependency; fresh fake manifest | Historical evidence preserved; changed dependency rejected before call; separate current fake campaign still exercises runtime validation |
| N1-33 | Check import direction and cancellation while adapter/verifier is running | No circular import; root lock is not held through external work; stale result cannot override cancellation |
| N1-34 | Root charges plus inclusive child/Controller reporting sample | Projection counts each charge once; unsupported live delegation/Controller remains disabled in N1 |

## Required walkthroughs and later owners

N0A's machine-readable design evidence records legal task-state witnesses for
first/second/third success, exhaustion, pending review, capability/verifier
recovery, uncertainty reconciliation, cancellation and partial closure. It also
records forbidden transitions and shows that v1 cannot express second-attempt
success. These validate the specification's graph, not OS races, receipts or
host enforcement. N1 must translate them into runtime tests with the guards.

N2 owns real DAG validation, child admission, depth/concurrency, exclusive
writes, parent cancellation and nested envelopes. N3 owns actual selector and
operator cell/policy overrides. N4 owns operational/public versus protected
grader separation, Graft oracle isolation, complete campaign manifests,
terminal campaigns and implementation/power validation of the statistical gate.
X2 owns legacy Controller identity mapping and task-wide counts. X4 owns
Controller integration, workflow/profile selection and interactive controls.

N1 exit requires all N1 rows passed with evidence, the full existing offline
harness, builder checks, consumer fake execution and a recorded migration/
rollback outcome. Unsupported host properties must remain explicit; do not
mark them verified because a fake model returned a well-formed receipt.
