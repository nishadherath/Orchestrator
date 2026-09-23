# Worker execution contract

Version: `worker-execution-contract-v1`. Frozen by Stage N0 on 2026-09-21.
Status: design contract for N1-N4; no production executor implements it yet.

This contract defines the task-level owner that the current routing system
lacks. It composes existing routing, acceptance, budget, registry and host
adapter primitives. It does not change B0, enable the Controller, launch a
worker or modify the consumer bundle.

## 1. Scope and invariants

The executor owns one admitted task revision from preparation through a
terminal result. Its durable record is authoritative for dispatch, accounting
and acceptance. Router output, worker prose and host lifecycle notices are
inputs to that record, never substitutes for it.

The following invariants apply to every implementation stage:

1. One `task_revision_id` has one active executor owner and one task budget.
2. Goal, acceptance, admitted inputs and operator permissions are immutable
   within a revision. A change creates a new revision linked to its parent.
3. A restart, session change, retry, repair, selected-cell change or host
   reconnect does not create a new task revision.
4. Dispatch intent and allowance are durable before the external side effect.
5. An `invocation_id` can start at most once. Ambiguous dispatch blocks further
   work until reconciled; absence of telemetry is never zero cost.
6. Only independently verified acceptance can produce `accepted`. Worker or
   router claims cannot complete the task.
7. A terminal stop remains terminal after restart. Continuation requires a new
   operator-authorised revision or a contract-defined non-terminal transition.
8. Requested and observed model identity, requested effort and observable
   effort evidence remain separate fields. Unsupported or mismatched identity
   cannot silently select another cell.
9. B0 stays `worker-sonnet-low`, one same-cell repair, then
   `worker-opus-high`, with at most three worker attempts and no Controller.
10. Child work consumes the parent's allowance and cannot weaken the parent's
    acceptance, permission or protected-path boundaries.

## 2. Existing components to reuse

| Concern | Existing owner | N1-N4 use |
| :--- | :--- | :--- |
| Qualified B0 sequence | `src/routing_priors.json`, `tools/route.py` | Load and pin the policy, never duplicate its constants |
| Cell identity and capability | `src/model_registry.json`, `tools/model_registry.py` | Resolve requested model/effort and qualification status |
| Acceptance freeze and evidence | `tools/acceptance.py` | Reuse `acceptance-v2`, contract digest and protected baseline |
| Durable allowance | `tools/dispatch_budget.py` | One budget scoped to the task revision; reserve, start and settle each invocation |
| Attempt record | `tools/route.py` version-2 ledger fields | Extend compatibly; keep existing evidence identity fields |
| Restricted subprocess execution | `tools/evaluation_live_worker.py` | Extract a production adapter rather than make evaluation code the owner |
| Crash-safe transition pattern | `tools/evaluation_live_episode.py` | Reuse journal-first transition and at-most-once dispatch techniques |

`tools/task_executor.py` is the proposed N1 owner. N1 may choose another name
only if repository inspection finds an existing production module with the same
responsibility. Evaluation runners must call the executor rather than copy it.

## 3. Versioned records

All records use canonical JSON for digests, reject unknown fields at ingress,
carry `schema_version: 1`, use project-relative paths and record UTC timestamps.
IDs are content-bound where stated and otherwise collision-resistant opaque
strings. Secrets and raw credentials are forbidden.

### 3.1 `TaskSpec`

The operator-admitted request. Required fields:

| Field | Contract |
| :--- | :--- |
| `task_id` | Stable logical task identifier |
| `goal` | Non-empty operator goal, bounded in size |
| `project_root` | Canonical execution root; stored as a manifest-relative identity, not a portable hard-coded path |
| `scope` | Allowed read/write paths and prohibited paths |
| `acceptance` | Complete value returned by `acceptance.load_contract()` |
| `permissions` | Operator-granted host/tool/network/external-side-effect limits and their provenance |
| `budget` | USD limit, deadline and optional token ceilings; unknown pricing stays explicit |
| `policy_request` | `qualified-default`, explicit policy id or explicit cell override with provenance |
| `input_revision` | Git HEAD plus diff/status digests, or equivalent content snapshot when Git is unavailable |
| `created_at` | Admission timestamp |

The frozen `task_spec_digest` covers every field except the timestamp. A caller
may propose assessment features, but cannot write acceptance, permissions or a
terminal outcome through this interface.

### 3.2 `TaskRevision`

Required fields: `task_revision_id`, `task_id`, `revision_number`,
`task_spec_digest`, `goal_digest`, `acceptance_digest`, `input_revision`,
`parent_revision_id`, `change_reason`, `authorising_actor` and `created_at`.

`task_revision_id` is the digest of task id, revision number, task-spec digest
and parent id. Valid reasons are `initial`, `operator-scope-change`,
`operator-acceptance-change`, `operator-input-change` and
`authorised-continuation`. Retry, repair, restart and model change are invalid
revision reasons.

### 3.3 `WorkerDecision`

Required fields: `decision_id`, `task_revision_id`, `policy_id`,
`policy_digest`, `assessment`, `assessment_provenance`, `selected_cell`,
`selected_cell_resolution`, `eligible_alternatives`, `rejections`,
`qualification_status`, `cost_projection`, `host_capability_digest`,
`override`, `created_at` and `decision_digest`.

The decision is advisory until the executor admits it. An override records
actor, scope, reason and requested value. Rejected or unavailable cells remain
visible. N3 owns selection logic; N1 initially accepts only the frozen B0
sequence or an explicit test fixture.

### 3.4 `AttemptResult`

This is a compatible superset of the version-2 route attempt. Required fields:

- `attempt_id`, sequence, invocation and parent invocation IDs;
- task revision, decision, budget and host-admission IDs;
- direct, repair, fallback or delegated start kind and its reason;
- requested cell, resolved CLI model, requested effort, actual model,
  effort evidence and identity verdict;
- start/finish timestamps, execution status, outcome and terminal flag;
- usage counters, cost, cost source, wall time and retained allowance;
- output/evidence references and digests, changed-path snapshot, boundary
  verdict, error class and reconciliation status.

Execution status is one of `prepared`, `admitted`, `running`, `verifying`,
`completed`, `failed`, `partial`, `blocked`, `cancelled` or `uncertain`.
Outcome remains `pass`, `fail` or `unknown`. A completed process with unknown
cost can have a terminal execution result but keeps accounting unresolved and
blocks learning and further paid dispatch.

### 3.5 `DelegationPlan`

N2 implements this record. Required fields are `plan_id`, `task_revision_id`,
`plan_digest`, `max_depth`, `max_concurrency`, `total_allowance_usd`, and a
bounded list of work items. Every work item contains its id, parent, dependencies,
goal, acceptance digest, requested cell or selector request, allowed reads,
exclusive writes, prohibited paths, allowance, deadline and return contract.

Validation rejects cycles, missing parents, overlapping concurrent writers,
scope expansion, child budgets exceeding the parent, child deadlines exceeding
the parent and recursion beyond the admitted depth. The empty plan means one
undivided task and must remain the cheapest path.

### 3.6 `HostCapability`

Required fields: `adapter_id`, `adapter_version`, host/version evidence,
supported launch mechanisms, available cells, enforceable command controls,
observable telemetry, lifecycle controls, concurrency, permission boundary,
receipt mechanism, unsupported properties and a canonical digest.

Capability is observed evidence scoped to a host version. It is not inferred
from documentation or from another agent platform.

## 4. Ownership and authority

| Actor | Owns | Cannot do |
| :--- | :--- | :--- |
| Operator | Goal, acceptance, permissions, explicit overrides, promotion | Rewrite recorded evidence or charges |
| Router/selector | Assessment and cell recommendation | Dispatch, grant permission or accept work |
| Executor | Task lock, state transitions, B0 attempt ceiling, budget and final status | Alter frozen acceptance or operator authority |
| Budget | Invocation allowance and reconciliation | Decide task success |
| Host adapter | One admitted side effect and its receipt | Retry, select another cell or claim acceptance |
| Verifier/reviewer | Acceptance evidence and decision | Launch work or alter artefacts |
| Worker | Produce bounded artefacts and an untrusted report | Accept itself, expand scope or authorise children |

Only the executor writes task state. Budget and acceptance modules remain the
single writers for their own records. Event records are append-only and linked
to the task revision and prior event digest.

## 5. Task state machine

| State | Permitted next states | Meaning |
| :--- | :--- | :--- |
| `prepared` | `admitted`, `blocked`, `cancelled` | Spec, acceptance and host capability validated |
| `admitted` | `running`, `blocked`, `cancelled`, `uncertain` | Owner lock, decision and allowance persisted |
| `running` | `verifying`, `failed`, `partial`, `blocked`, `cancelled`, `uncertain` | Dispatch intent persisted and one host action may be in flight |
| `verifying` | `accepted`, `failed`, `partial`, `blocked`, `uncertain` | Terminal attempt exists; independent acceptance owns the result |
| `accepted` | none | Acceptance passed and accounting is reconciled |
| `failed` | none | Attempt policy exhausted or verified failure is terminal |
| `partial` | none | Useful evidence exists but acceptance is incomplete |
| `blocked` | none | A required permission, capability, budget or verifier is unavailable |
| `cancelled` | none | Operator cancellation; in-flight allowances remain until reconciled |
| `uncertain` | none | Dispatch or accounting cannot be proven terminal |

`failed`, `partial`, `blocked`, `cancelled` and `uncertain` may inform a newly
authorised revision, but reopening the same terminal record is forbidden.
`accepted` is immutable.

For one attempt the durable order is: validate revision and lock; persist
decision; reserve allowance; persist admission; mark invocation started;
persist dispatch intent; call the adapter once; persist raw receipt and actor
snapshot; settle or retain the allowance; run acceptance; persist terminal
state; release the task lock. A crash between intent and receipt recovers to
`uncertain`, never to a new dispatch.

## 6. B0 execution contract

The exact maximum sequence is:

1. `worker-sonnet-low`, reason `fixed_floor`;
2. `worker-sonnet-low`, reason `one_local_repair`, only after observable failure
   and with the first attempt's output and failure evidence preserved;
3. `worker-opus-high`, reason `fixed_fallback`.

Stop immediately on independently verified acceptance. Do not run the repair
for infrastructure, permission, identity or accounting failure. Those produce
`blocked` or `uncertain`. After the third verified failure, terminate `failed`
with reason `fixed_fallback_exhausted`. No branch invokes Controller or an
unlisted worker.

## 7. Host capability boundary

The current repository supports these distinct mechanisms:

| Mechanism | Enforceable now | Not established |
| :--- | :--- | :--- |
| Restricted Claude CLI subprocess | Working directory, explicit model and effort arguments, budget argument, tool list, timeout; streamed served-model and usage evidence when supplied | Independent served-effort telemetry, invoice-finality after interruption, arbitrary filesystem interception |
| Interactive Claude Agent/Task | Worker definition selects cell; start/message/stop/resume lifecycle; ledger can record an admission before a cooperative launch | Atomic prevention of an unmanaged launch, automatic receipt reconciliation, programmatic access to the human `/tasks` panel |
| Current Codex development session | Repository editing and local checks in this workspace | Equivalence to Claude worker definitions; verified GPT-5.6 Sol identity or effort telemetry |

N1 must expose unsupported capabilities as explicit blocked or interactive
states. It must not describe a prompt obligation as host enforcement. An
interactive launch uses an executor-issued admission token and requires a
matching receipt before verification. A programmatic adapter uses the same
token and receipt schema.

## 8. Recovery, migration and rollback

- A missing state file creates a new task only from a valid `TaskSpec`.
- A matching state file resumes deterministic local transitions. A digest
  mismatch blocks as foreign state.
- `running` without a terminal receipt becomes `uncertain`; reconciliation may
  settle cost but may not redispatch the invocation.
- A committed receipt not yet placed in history is replayed locally and
  idempotently, without calling the host.
- Corrupt budget, acceptance, event chain, identity or task state fails closed.
- Existing version-2 routing ledger entries remain readable. New fields live in
  executor evidence until a later migration is specified and tested.
- Rollback disables the new executor entry point and restores the current B0
  interactive instructions. It never deletes task, budget or acceptance data.
- N1 provides a dry-run migration/compatibility report before any persistent
  format change. No migration is part of N0.

## 9. Required stage evidence

N1 must test every task transition, exact B0 ceiling, concurrent admission,
crashes before and after dispatch, timeout and unknown cost, identity mismatch,
duplicate and conflicting receipts, protected-path changes and idempotent local
recovery. N2 adds DAG, ownership, nested-budget, cancellation and aggregation
tests. N3 adds all-cell selection, rejection and wording-invariance tests. N4
uses this executor for fake campaigns and proves terminal campaigns admit zero
new calls after restart.

These checks qualify mechanics. They do not establish that a cell is available,
that effort was served, that selection improves quality or that a new default
should ship.

## 10. Evaluation gate frozen by N0

The task, not a repetition, is the independent unit. A regression event is a
reserved task for which B0 is accepted and the candidate is not, after the
predeclared repetition aggregation. Use a one-sided exact Clopper-Pearson upper
bound for its population rate. With zero observed regressions, the bound is
`1 - 0.05^(1/n)`: 22.1% at 12 tasks and below 5% first at 59 tasks.

Therefore the planned 12-task N6 run is exploratory and cannot by itself
qualify the 5 percentage-point no-harm claim. Before N5 spend, choose one:

- freeze at least 59 genuinely independent reserved task mechanisms, with the
  final minimum increased if pilot variance, any regression or multiplicity
  adjustment requires it; or
- retain the capped campaign, label it exploratory and make B0 retention the
  only permitted release decision.

For paired quality, use a predeclared one-sided paired interval over task-level
aggregates. N4/N5 must simulate power using development variance before the
reserved manifest is frozen. Control the family-wise error of the acceptance
and quality claims with Holm at 0.05. Critical violations and false-success
increases are hard zero-tolerance gates. Cost and latency remain fully reported;
the 10% cost branch is descriptive unless an inferential cost gate is separately
frozen before reserved results.

