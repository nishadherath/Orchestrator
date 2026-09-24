# Managed delegation

`tools/managed_delegation.py` adds an explicit child plan to an admitted
`TaskExecutor` root. Ordinary B0 routing does not create a plan. The root owns
progression, cancellation, final acceptance and one monetary balance. Children
have one admitted worker call each; they cannot spawn further workers. A nested
plan is a static graph approved before any call, not recursive model-directed
spawning. The Controller is never invoked by this path.

## Admission and execution

Create the root with `TaskExecutor.admit(...)`, then, before its first B0 call,
pass a version 1 proposal to `ManagedDelegation(executor).admit(root_id,
proposal, actor=..., authority_id=...)`. Call `managed.run(root_id)` to execute
ready child waves. It returns the root record and budget snapshot. All required
children must independently pass their frozen acceptance before
`executor.run(root_id)` can complete the parent through B0. A child review
uses `managed.review_child(...)`; an uncertain child requires
`managed.reconcile_child(...)` with a known charge and stopped-writer proof.
Neither operation silently relaunches a worker.

```json
{
  "version": 1,
  "max_depth": 1,
  "max_concurrency": 1,
  "parent_reserve_usd": 0.25,
  "parallel_reason": "",
  "items": [
    {
      "id": "tests",
      "parent_id": null,
      "depends_on": [],
      "goal": "Implement the public tests",
      "reads": ["spec.txt"],
      "writes": ["tests/test_feature.py"],
      "permissions": ["read", "edit"],
      "acceptance_path": "child-acceptance.json",
      "requested_cell": "worker-sonnet-low",
      "allowance_usd": 0.20,
      "envelope_usd": 0.20,
      "deadline_at": null,
      "return_contract": "verified_acceptance"
    }
  ]
}
```

The operator supplies this proposal and authority. Treat a model-generated
proposal as untrusted input. Every item requires the exact fields shown. Reads
must fit the root's write scope or frozen input paths; writes and required
outputs must fit the root's write scope. Child writes cannot touch protected
paths or executor state. Dependencies and parent links must name items in the
same plan. Cycles, concurrent read/write conflicts, unsafe paths, unknown cells,
missing contracts and budget oversubscription are rejected before a child
launch. Conflicting writers may be sequenced by an explicit dependency. A
nested child must explicitly depend on its executing parent. An expired
required child deadline cancels the root and stops new admissions. A
parallel plan needs an operator-stated latency or isolation reason.

`allowance_usd` caps one child's provider call. `envelope_usd` caps that item
and all its nested descendants; top-level envelopes plus
`parent_reserve_usd` must fit the root's available balance. The budget module
reserves each child call exactly once against that balance. Envelopes are
limits, not additional charges or holds. Unused, never-started child
reservations settle at measured zero if the plan blocks or is cancelled.
Unknown post-dispatch cost retains its hold. Root completion needs the reserved
headroom and verifies every accepted child's outputs still match its evidence.

Depth and concurrency are bounded by both the proposal and tested host
capability. The production `WorkerAdapter` currently reports
`managed_delegation_enforced: false`: its restricted tool list and scoped Graft
configuration do not prove filesystem isolation or interception of arbitrary
interactive Agent launches. Admission therefore rejects this managed path on
that host. Offline fake-host tests validate graph, recovery and accounting
behaviour, not live Claude enforcement. N4 owns the live isolation proof.

An executor process crash after a child intent leaves an unresolved call,
never an automatic retry. Persisted terminal receipts can be settled and
verified on restart. Cancellation signals active local processes, stops new
children and preserves late charges. Inspect the root journal and budget under
`.claude/task-executor-v2/`, and run
`python3 tools/task_executor.py --audit --project .` before rollback or legacy
relaunch. Keep those records intact until every writer and hold is reconciled.
