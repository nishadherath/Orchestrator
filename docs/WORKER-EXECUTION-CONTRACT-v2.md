# Worker execution contract v2

Version: `worker-execution-contract-v2`, amended by N0A on 2026-09-24.
Status: **N1 and N2 implemented and qualified offline; N3-N4 extensions pending**.
This replaces [v1](history/WORKER-EXECUTION-CONTRACT-v1.md) for N1 onward.
The [N0A record](stage-results/worker-n0a.md) explains the changes and evidence.
The [acceptance matrix](WORKER-N1-ACCEPTANCE-v2.md) and
[N1 result](stage-results/worker-n1.md) record the implementation gate.

## 1. Scope and ownership

N1 implements an executor and production adapter; N2 adds managed delegation;
N3 adds candidate selection; N4 adds campaigns. B0 remains the qualified default.
No N-series path invokes Controller, including errors or fallback. X2/X4 later
reuse the identity, allowance and extension contracts here.

| Owner | Sole writable authority | Boundary |
| :--- | :--- | :--- |
| Operator | Authorised goal, scope, permissions, overrides, budget changes and promotion | Cannot rewrite evidence or charges |
| Executor | Root admission, revision lifecycle, owner generation, decisions and attempt journal | Cannot grant permissions or accept worker claims |
| Budget module | Root monetary balance, reservations, settlement and authorised limit changes | Cannot choose policy or decide acceptance |
| Acceptance module | Verification/review evidence for a frozen contract | Cannot dispatch or modify task outputs |
| Selector | Advisory assessment and cell recommendation | Cannot admit work or change task identity |
| Host adapter | One admitted side effect, receipt and termination evidence | Cannot retry, choose another cell, accept work or spawn unmanaged children |
| Worker | Bounded artefacts and untrusted report | Cannot change authority, frozen acceptance or final status |
| Future Controller adapter | Allocated Controller execution and returned evidence | Cannot own the overall task or a second root balance |

Use `tools/task_executor.py` and `tools/worker_adapter.py` as N1 module names.
Reuse `route.py`, `model_registry.py`, `dispatch_budget.py` and `acceptance.py`.
Do not copy their policy, identity, accounting or verification logic.

## 2. Identity and records

New executor records carry `schema_version: 2` and an explicit record type;
existing route-ledger-v2 and acceptance-v2 keep their own versions. Canonical
JSON uses sorted keys, compact separators, UTF-8, no NaN, and SHA-256. Reject
unknown fields at ingress; bounded strings, UTC timestamps and project-relative
artefact paths are required. Credentials never enter records. Local execution
root resolution is trusted configuration, not worker-supplied path authority.

### Immutable definition and mutable evidence

`TaskDefinition` contains `project_id`, `root_task_id`, `task_id`, optional
`parent_task_id`, `goal`, `scope`, `permissions`, `input_revision`, and
`acceptance_definition`. `project_id` is a persisted project identifier bound
to the local root, not an absolute path embedded in a portable contract.
Root/task ids are collision-resistant opaque ids, never chosen to reset limits.

`acceptance_definition` contains only `contract_version`, `contract`,
`contract_digest` and `protected_baseline` from `acceptance.load_contract()`.
Mutable `status`, `evidence` and `review` belong to per-attempt AcceptanceState.
Load/freeze the protected baseline once per admitted revision. Never reload
after a worker edit to make a modified protected path the new baseline.

The definition digest covers exactly the fields above, including null parent.
`TaskRevision` binds definition digest, positive `revision_number`, parent
revision id, `change_reason` and authority reference. Its id is the digest of
that tuple plus `task_id`. Timestamp is excluded. Revision reasons are initial,
operator-goal/scope/permissions/acceptance/input-change, and
authorised-continuation. Repair, restart, model/effort change and review are
not revision reasons. Worker outputs during an attempt do not redefine its
admitted input snapshot. Unexpected external edits invalidate the evidence.

`TaskAdmission` separately binds revision id, initial policy request, initial
budget authority, host capability digest, actor and timestamp. A later
`OverrideEvent` records actor, scope, reason, requested policy/cell and decision
generation. It changes only a future decision, never an active invocation or
the definition digest. N1 rejects non-B0 execution overrides as unsupported;
N3 implements them as explicitly experimental, without default promotion.

`WorkerDecision` records revision id, attempt sequence, policy id/digest,
assessment/provenance, selected cell and registry resolution, eligibility and
rejections, qualification, cost projection, capability digest, override event
and its own digest. A decision is advisory until admission commits it. Pin B0
from the current qualified policy data; do not duplicate a model ladder.

`AttemptResult` is an executor sidecar, **not** a superset accepted directly by
the legacy ledger. It binds task/revision/decision ids, attempt sequence,
invocation and optional parent invocation, admission token, budget allocation,
intent, receipt, process status, requested cell/model/effort, observed model,
effort evidence, timestamps, usage/cost/source, retained allowance, artefact
snapshots, error class, verification and reconciliation evidence. Rich reasons
are `fixed_floor`, `one_local_repair`, `fixed_fallback`, or later explicit
override/delegation reasons. Unknown cost is null, never inferred zero.

`TaskSnapshot` binds root/task/revision ids, lifecycle state, owner and decision
generations, last event sequence/digest, current attempt/invocation, consumed
dispatch slots, budget reference, cancellation generation and any block's
reason/resume phase. It is a recoverable projection of the journal, not a second
source of authority. Missing snapshot plus existing journal/budget means recovery,
not a fresh task. Missing or corrupt root admission history fails closed.

An invocation id is globally unique within the root. Its immutable receipt
digest is separate from subsequent reconciliation events. An identical receipt
is idempotent; a different receipt for the same id is a conflict requiring
investigation. New reconciliation evidence appends a linked event, not a
replacement receipt. Acceptance evidence uses a unique per-attempt entry id.

### Continuation and legacy identity

An authorised continuation creates a successor revision under the same task
and root, with a new snapshot/authority reference. It may begin only after
the predecessor is terminal, all affected writers are proven stopped, and
all root uncertainty/holds are reconciled. It does not erase charges. A normal
retry or a resolved review stays within the existing revision.

Example: task T/revision R1 fails its first verified attempt; repair remains
R1 with a new invocation. A cell override remains R1 with a new decision.
An operator changes acceptance: close R1 explicitly and admit R2 linked to R1,
retaining T's spend. A child has its own task/revision but the same root budget.
Copying T's goal into a new id is not an authorised way to continue T.

X2/X4 must retain the legacy Controller hash (problem text plus resolved
project/input identity) and bind it to the v2 revision with a versioned mapping
record: old id, v2 id, root id, acceptance digest, input digest and authority.
Validate the legacy packet in its original namespace, then the mapping. Never
substitute a new id into historical evidence. A legacy hash can coincide for
different acceptance contracts, so it alone cannot authorise v2 work. X2 owns
durable Controller admission counts; counts cannot reset through decision ids,
overrides or a fabricated input revision. Further interventions need explicit
recorded authority and remaining or added root allowance.

## 3. Task lifecycle

The table is the complete allowed edge set. Every edge additionally requires
the guard below. Same-state journal/accounting events are not lifecycle edges.
Any unlisted edge is rejected. Terminal task states have no outgoing edges.

| State | Permitted next states | Meaning |
| :--- | :--- | :--- |
| `prepared` | `ready`, `blocked`, `cancelled` | Definition and authority being validated |
| `ready` | `admitted`, `blocked`, `cancelled` | Next permitted attempt selected; no side effect yet |
| `admitted` | `running`, `blocked`, `uncertain`, `cancelled` | Durable reservation and immutable admission exist |
| `running` | `verifying`, `blocked`, `uncertain`, `cancelled` | Intent committed; host action may exist |
| `verifying` | `ready`, `awaiting_review`, `accepted`, `failed`, `partial`, `blocked`, `uncertain`, `cancelled` | Complete receipt; verification decides next action |
| `awaiting_review` | `verifying`, `blocked`, `cancelled` | Required independent review is pending |
| `blocked` | `ready`, `verifying`, `awaiting_review`, `uncertain`, `failed`, `partial`, `cancelled` | Known impediment; no dispatch while blocked |
| `uncertain` | `verifying`, `blocked`, `cancelled` | Dispatch, writer termination or accounting unresolved |
| `accepted` | none | Verified pass and fully reconciled task |
| `failed` | none | Exhausted policy or authorised terminal failure |
| `partial` | none | Authorised terminal incomplete result with useful evidence |
| `cancelled` | none | Operator/deadline stop; accounting may still need reconciliation |

Guards and authority:

- `prepared -> ready` requires validated immutable inputs, permissions,
  acceptance and host capability, plus no root uncertainty or conflicting writer.
- `ready -> admitted` atomically checks root budget, active owner generation,
  decision generation, cancellation, permissions and policy attempt ceiling.
- `admitted -> running` requires `budget.start(invocation_id)` and durable
  dispatch intent before the host call. This consumes the attempt's dispatch
  slot, even if a crash leaves it unknown whether the host received the call.
- `running -> verifying` requires identity-valid terminal receipt, proof the
  writer stopped and final cost evidence. Unknown fields route to `uncertain`;
  a known identity/protocol/permission fault routes to `blocked`.
- `verifying -> ready` requires an ordinary verified quality failure, no
  protected-boundary violation, complete accounting, unchanged acceptance and
  an unused B0 successor slot. Record the failure and retain its output first.
- `verifying -> accepted` requires independent pass, valid identity, stopped
  writers, no unresolved reservations and intact evidence/protected paths.
- Rubric `review_required` gives `awaiting_review`; a signed review returns to
  `verifying` on the same revision and attempt. Recheck artefact digests.
- A blocked record stores `reason`, `resume_phase` and evidence needed to clear
  it. Resumption requires an explicit operator resume event and proof the
  impediment is resolved. Pre-dispatch blocks may return to `ready` after any
  abandoned reservation is proven unused and released. Verifier-only blocks
  return to `verifying` or `awaiting_review` without another worker call.
- A post-dispatch infrastructure/permission/identity fault does not authorise
  quality repair. Only a validated correction of the existing receipt may
  permit verification; otherwise close failed/partial/cancelled. A fresh
  execution requires an authorised continuation after safe reconciliation.
- `uncertain` cannot lead directly to admission. Append proven settlement and
  writer-termination evidence, then require operator resume to verify the same
  attempt or enter a known blocked state. No automatic replay of the invocation.
- `failed` after B0 exhaustion is automatic. Early `failed`/`partial` closure
  from verifying/blocked requires operator finalisation and stopped writers,
  known accounting and a reason. Partial is never a pass. `cancelled` can be
  entered immediately, but holds/writer barriers survive its terminal status.
- Every non-terminal state permits cancellation as listed. Deadlines use this
  stop path. Accounting updates to a terminal record do not reopen its task.

Attempt process states are separately `reserved`, `intent_committed`,
`terminal` and `uncertain`. Process termination, verification and accounting
are separate facts, not one success flag. A terminal failed attempt can be
followed by another attempt while the task remains non-terminal.

## 4. B0, locking and recovery

B0 remains Sonnet Low, one Sonnet Low repair after observable quality failure,
then Opus High. Maximum three dispatch intents; stop on independently verified
acceptance. Store the actual three pinned cells in the decision evidence.
Overrides and delegation are not a hidden extension to B0's attempt ceiling.

The executor maintains a project-level admission/writer registry above roots.
It binds root creation to operator authority and arbitrates overlapping write
scopes across different roots as well as revisions. Unresolved writer claims
survive cancellation and cannot be evaded by selecting another task/root id.
Independent roots may run only with non-conflicting scopes and separately
authorised budgets. Reusing root-creation authority with a different root is
a conflict, not another grant. No comparison of natural-language goals is used
as an identity or permission mechanism.

One root OS coordination lock serialises admission/recovery/authority changes;
one durable owner generation fences stale executor callbacks. Release the OS
lock during host calls, but retain durable ownership and workspace claims.
Acquire locks in order: project admission registry, root coordination, budget,
acceptance/route ledger. Hold multiple roots only in sorted-id order.
No module holding a lower lock may call back into the root owner. A lock's
expiry or a dead launcher alone does not prove that an external writer stopped.
Neither adapter calls nor external verifier commands hold these OS locks;
returned results must pass the ownership/generation checks. Cancellation can
acquire the coordination lock and signal the adapter while
the call runs; late receipts are reconciled, never discarded as free.

Journal order: persist decision and reservation intent; reserve budget;
persist admission; commit budget start; persist host dispatch intent; call
adapter once; persist raw receipt and stopped-writer evidence; settle budget;
verify frozen acceptance; append next task transition. Journal events carry
sequence, prior digest and operation id for idempotent local recovery.

Recovery rules close cross-file crash windows:

| Durable evidence after crash | Recovery |
| :--- | :--- |
| Decision only, no reservation | Revalidate locally; no host call has occurred |
| Budget reserved, admission journal missing | Join by invocation/operation id; do not reserve twice |
| Reservation with no budget start or host intent | Under root lock prove no active dispatcher; settle measured zero with local pre-dispatch evidence, abandon id, permit fresh admission in the same unused slot |
| Budget start committed, host intent missing | Treat as uncertain; never call the host on replay |
| Host intent committed, receipt missing | Retain full unresolved allowance and writer barrier; reconcile externally |
| Receipt persisted, settlement/transition missing | Replay settlement and local verification idempotently, no host call |
| Terminal task plus late receipt | Reconcile accounting only; task remains terminal |
| Corrupt identity/journal/budget or conflicting receipt | Fail closed, preserve evidence and root holds |

Actual host calls cannot be guaranteed exactly once after an ambiguous crash.
The guarantee is at-most-once executor dispatch per invocation, with uncertainty
made explicit. Snapshot artefacts before another attempt can overwrite them.
Operational verification runs once per evidence generation. Retrying a blocked
verifier needs explicit authority; verifier commands must be predeclared and
must not grant new worker/network permissions.

## 5. One root budget across revisions and children

Use the existing `DispatchBudget` with `scope="task_dispatch"` at a stable
root-task location; revision ids never choose a new balance. Keep integer
nanodollars and separate known charges from unresolved holds. Available funds
are limit minus charges minus holds. All assessor, worker, verifier and future
Controller provider calls require admitted allocations, not only worker calls.

N1 must add tested, backward-compatible budget lifecycle operations for explicit
limit amendments and authorised continuation after cancellation. Do not change
existing `__init__`, `reserve`, `start`, `settle` or `cancel` semantics for old
callers. Limit amendment records previous/new limits, actor, authority id,
reason and expected budget generation; it never resets charges or holds.
Initial support increases limits only. Duplicate authority ids are idempotent;
conflicting reuse is rejected. Normal reopen still rejects a changed limit.

Cancellation closes an execution generation. A successor generation requires
explicit continuation authority, a terminal predecessor, all stopped writers
and reconciled holds. It retains the same root balance and immutable history;
it cannot revive the predecessor or its invocation ids. This operation belongs
to the budget module under the root lock, not direct executor JSON edits.
New audit metadata must remain readable by old callers, or N1 must introduce
an explicit versioned migration with backup/dry-run and fail-closed rollback.

N2 child envelopes and X4 Controller envelopes reserve against the root once.
An envelope's inner charges are detail, not extra root charges. Each provider
charge has one owning allocation and stable receipt identity. The root retains
the envelope hold until the child/Controller subledger is reconciled. Never
sum an inclusive parent charge and the same descendant charges again. Unknown
aggregation is a block, not permission to pick the cheaper total.

## 6. Legacy ledger projection

Keep executor sidecars authoritative. Export an allowlisted route-v2 projection
through the existing normalisation path; never pass rich sidecars directly.

| Executor fact | Route-v2 projection |
| :--- | :--- |
| Reserved before intent | `execution_status: pending`, outcome unknown |
| Intent committed with observed active process | `running`, outcome unknown |
| Terminal process completed normally | `completed`; outcome from independent acceptance, otherwise unknown |
| Terminal process error/nonzero exit | `failed`; outcome fail only if independently established |
| Cancellation with proved termination | `cancelled`, outcome unknown unless prior evidence establishes fail |
| Ambiguous interruption, timeout or lost receipt | `interrupted`, outcome unknown; no learning eligibility |

The legacy normaliser assigns `id=att-NNN`, `sequence`, and start kind direct
for the first attempt or escalation thereafter. Preserve that representation;
repair/fallback/delegation semantics stay in the sidecar. Export only existing
invocation/parent ids, requested cell, actual model, effort evidence, bundle and
policy versions, timestamps, process status, outcome, wall time and usage fields.
Cost source remains provider_reported, price_derived, measured_zero or unknown.
Partial task completion is not legacy pass. A projection must not bypass
`acceptance.qualified()` or admit uncertain evidence to capability learning.
Terminal ledger entries are not rewritten to pretend late evidence existed
earlier; append linked reconciliation evidence and exclude unresolved entries.

## 7. Adapter and distribution boundary

`worker_adapter.py` owns WorkerRequest, command construction, stream parsing
and single-call receipt normalisation extracted from `evaluation_live_worker.py`.
The latter retains evaluation fixtures, qualification and compatible imports.
Production adapter imports standard library and production model registry
only, plus a small production record helper if necessary. No `test/`,
`realworld`, calibration result file or Controller runtime import is permitted.

Add executor, adapter and any new production helper/schema to
`build_dist.planned_files()`. N1 tests imports and a fake complete task from
an isolated installation with the repository and test tree unavailable.
Do not defer discovering an installation dependency until N8. Existing budget
imports route helpers; keep the executor above both modules. Avoid top-level
route-to-executor imports. Extract common persistence only if a concrete cycle
requires it, retaining legacy re-exports and regression tests.

HostRequest binds admission token, root/revision/invocation ids, intent digest,
decision/capability digests, exact cell/effort, actor root, scope, permitted
tools, allowance, deadline and task payload. Receipt echoes those identities,
actual command contract, observed model/effort evidence, usage, cost, process
termination and artefact references. Executor verifies the match before use.
Tokens are opaque, single-use and backed by executor state, not a bearer grant
to exceed host permissions. Diagnostic output names unsupported capabilities.

Restricted CLI tools do not establish arbitrary filesystem sandboxing.
HostCapability must distinguish configured controls from proven enforcement.
Managed evaluation requires an isolated actor root containing public material
only, with protected grading outside every actor-accessible mount/process.
Inherited environment/instructions and tool settings are part of the manifest.

Each managed worker must have the required six Graft retrieval tools bound to
its actor/project root. Use explicit MCP configuration and a tool allowlist;
do not enable every MCP server. Graft search, graph, cache and semantic summaries
must contain only actor-visible data. A root argument or prompt alone is not
proof of isolation. N1 exposes capability and fake tests; N4 proves isolation
against sentinel oracle material. If the host cannot provide required Graft or
isolation, block that managed path. Do not silently skip Graft or claim testing
the historical restricted adapter established this capability.

Interactive launches use the same admission and matching receipt. The executor
cannot currently intercept arbitrary human Agent/Task launches; label those
unmanaged and exclude them from enforced dispatch/qualification claims. No
equivalence between Codex development agents and Claude worker definitions is
assumed. Served effort is unknown unless the provider supplies independent
evidence; CLI arguments prove requested effort only.

## 8. Optional Controller step, implemented by X4

The executor admits a Controller request against a root allocation, invokes
the Controller adapter and consumes its validated evidence. Do not wrap the
entire existing per-decision TaskDispatcher as a second root owner. X4 adapts
the inner execution boundary and preserves the legacy direct interface.
The request binds revision mapping, acceptance digest, role profile, allowance,
deadline, permissions and cancellation. Its receipt binds evidence packet,
inner accounting, actual role identities and terminal/writer status.

Controller output can recommend further work, clarification or stopping. It
cannot alter acceptance or declare task success. The executor then admits a
worker or returns an incomplete result. Reserve worker continuation allowance
before admitting Controller work. X2 enforces task-wide Controller admissions;
X4 implements workflow/profile selection and interactive auto/on/off. N1 needs
only these documented interfaces and zero-Controller-call tests, not a plugin
framework or live Controller implementation.

## 9. Frozen evidence and current tests

N1 owns the test-compatibility split, without changing Controller runtime:

1. Historical tests validate committed manifest self-digests, authorisation and
   recorded artefact linkage against the recorded baseline. Verify bound source
   bytes from that baseline or a pinned immutable snapshot, not current hashes.
2. Current-code fake tests construct separately named temporary manifests and
   offline-only authorisations. Bind current files, preserve schedule/ceiling
   validation and inject fake transports. Never write over an old manifest or
   re-use its live authorisation. Do not mark these tests as historical runs.
3. Mutation tests alter a bound dependency in a temporary fixture and verify
   admission rejects it before any adapter call. Historical manifests presented
   to a changed runtime must still fail. No mock that skips hash validation.

If a baseline object is unavailable, obtain a verified pinned snapshot before
closing the historical check; do not silently skip it. Test-only fixture/helper
changes are permitted in N1/N3. Controller stop/resume algorithms remain X1.
Do not execute old R5 live campaigns. New worker campaign machinery is N4;
X1 reuses it, X3 also requires N3, and X4 owns end-to-end integration before X5.

## 10. Acceptance, grading and statistical gate

Operational acceptance is the frozen operator contract executed independently
of worker claims. Its public tests or rubric may establish operational pass;
being public is not itself a defect. Benchmark correctness is a distinct,
protected post-episode grade. That grade and family labels cannot steer retry,
model selection, assessment, clarification or Controller decisions in either
arm. Track operational false success against the protected grade separately.

N0A replaces v1's gross-regression proxy with the original plan's net paired
acceptance estimand. The 59-task figure in v1 applies only to a one-sided 95%
zero-event bound on B0-only successes. It is not a universal sample requirement
for net paired non-inferiority or quality improvement.

Freeze this conservative default analysis for N4 to implement and validate:

- Independent unit: task mechanism, not repetition. Each arm has two scheduled
  repetitions. Task acceptance is one only if both protected grades accept;
  task quality is their mean on a bounded 0-100 rubric. Missing/unfinished
  scheduled repetitions count as not accepted; grade available artefacts for
  partial quality, zero if none. Missing grader integrity makes the comparison
  inconclusive, not zero. Retain all actual/unknown costs.
- Net acceptance delta is P(candidate-only accepted) minus P(B0-only accepted).
  Let w/l be those task counts out of n. Set alpha_A=.025. Compute
  `L_A = CP_lower(w,n,.0125) - CP_upper(l,n,.0125)`, where each CP endpoint is
  one-sided at the specified tail probability. Use lower=0 at w=0 and upper=1
  at l=n. Otherwise invert the binomial tails, or equivalent beta quantiles:
  lower `BetaQuantile(a,k,n-k+1)`; upper `BetaQuantile(1-a,k+1,n-k)`.
- For paired quality differences D_i in [-100,100], use
  `L_Q = max(-100, mean(D) - 200*sqrt(log(1/.025)/(2*n)))`.
  This is a conservative bounded-variable lower confidence bound. The two
  .025 error allocations give at least 95% simultaneous coverage by the union
  bound, replacing v1's unspecified Holm implementation. Report point estimates
  and these bounds, not only a pass/fail verdict.
- Promotion requires L_A > -.05 and L_Q > -5, no candidate critical violation
  and no increase in false-success count, plus either observed total cost <=.9
  times B0, or L_Q > 5 with cost <=1.25 times B0. Baseline cost must be known
  and positive for a cost ratio; missing costs block promotion. Cost ratios are
  descriptive gates, not population cost-effectiveness claims. Operator
  promotion remains separate from statistical eligibility.

The CP construction assumes independent tasks sampled from the declared target
distribution; Hoeffding requires independent bounded task differences. A curated
suite without a defensible sampling frame supports suite results, not universal
real-world claims. N4 documents that frame, grade bounds and independence;
N4/N5 simulate power on development data. The conservative bounds may be
inconclusive at 12 tasks; retain B0 rather than automatically buy more samples.
A more efficient validated method needs a versioned, operator-reviewed amendment
before N5 spend and before any reserved results are visible. No retrospective
method selection, threshold relaxation or automatic sample expansion.

Sources: [NIST exact binomial intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
for tail inversion; [Hoeffding (1963), theorem 2](https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf)
for bounded independent sums. The paired combination and error allocation above
are this contract's design choices. They are not measured power results.

## 11. Stage boundaries and rollback

N1 implements and tests sections 1-7 and the acceptance matrix. N2 adds DAGs,
exclusive writers, child receipts, root accounting and cancellation. N3 adds
selection and overrides; N4 adds protected campaigns and statistical code.
N0A's walkthrough evidence verifies the design only, not these implementations.

Rollback disables new executor entry points and restores qualified B0 consumer
instructions. It never deletes tasks, receipts, reservations or acceptance
evidence. Outstanding managed tasks remain blocked until reconciled; reverting
an entry point is not permission to relaunch them through legacy instructions.
An old reader must reject unsupported state rather than reset it. N1 provides
a dry-run compatibility report before any persistent format migration.
