# Controller report, 20260928T083641-1415bed4

Outcome: gap. Mode: quick. Calls: 11. Cost: USD 1.6523. Ledger frozen at v2.

## No solution

Termination: budget_spent.
Next cheapest test: none

## Acceptance criteria

- Each candidate cause is paired with at least one check whose outcomes differ across causes, with the discriminating outcome stated
- The candidate set is explicitly assessed for closure, including any cause outside the three named
- A containment step is proposed with its reversal stated and its cost to correctness named
- The implementation direction is stated as conditional on a named check result, with the condition explicit
- No check is reported as run, and no outcome is asserted as observed
- Every claim is traceable to the problem statement or marked as an assumption

## Premise ledger

Every premise at the frozen version, with the class verification left it in.

- prem-001 [unverified, confidence 0.85]: A job acknowledgement and its receipt write target two separate stores, so the two operations are not covered by a single commit.
- prem-005 [unverified, confidence 0.7]: An idempotency check exists on the write path and is capable of suppressing a retry, since it is offered as a candidate cause.
- prem-006 [unverified, confidence 0.65]: Retries occur on the write path, and at least some are legitimate rather than duplicates; without retries the suppression explanation is void.
- prem-007 [habit, confidence 0.6]: An acknowledgement without a durable receipt is treated as a defect, which presumes an unstated invariant that acknowledgement implies receipt durability.
- prem-008 [policy, confidence 0.95]: Only the supplied statement may be used as evidence; no other fixture source, log or repository file may be consulted.
- prem-009 [policy, confidence 0.95]: No check may be reported as executed and no outcome asserted as observed; proposed checks stay hypothetical.
- prem-011 [verified, confidence 0.9]: No concrete occurrence is available: the statement asserts only that a receipt can be absent after an acknowledgement. No job id, log excerpt or observation record exists, so the symptom is a stated possibility, not a measured event.
- prem-012 [verified, confidence 0.95]: The available notes do not determine the cause. problem.md contains the statement plus task instructions only, with no field, status or log excerpt selecting writer failure, premature acknowledgement or idempotency suppression.
- prem-013 [verified, confidence 0.9]: The three named explanations are not exhaustive. Enumeration adds a stale or wrong-replica read, replication lag, and retention or expiry deleting a committed receipt; none collapses into the three, and the statement uses no closure language.
- prem-014 [verified, confidence 0.9]: No fixture artefact beyond the 14-line statement exists: no writer code, idempotency branch, retry policy or log. Every check the brief proposes is therefore a design, unrunnable here, and prem-001, prem-005 and prem-006 cannot be closed.
- prem-015 [verified, confidence 0.9]: The statement declares a synthetic fixture with no production system or customer data and an investigation-brief deliverable, and no live endpoint, dataset or code binding exists in the working directory, so containment carries no live blast radius.

## Unverified load-bearing premises

- prem-001: A job acknowledgement and its receipt write target two separate stores, so the two operations are not covered by a single commit. (cheapest verification: Read the fixture's writer path and confirm no shared transaction or outbox spans the queue ack and the receipt store.)
- prem-005: An idempotency check exists on the write path and is capable of suppressing a retry, since it is offered as a candidate cause. (cheapest verification: Locate the idempotency key derivation and the suppression branch in the fixture writer code.)
- prem-006: Retries occur on the write path, and at least some are legitimate rather than duplicates; without retries the suppression explanation is void. (cheapest verification: Check the fixture for a retry policy and for any record of a retry attempt on an affected job id.)

## Ranked alternatives

- none shortlisted above the baseline

## Audit trail

(none)

## Dispatch accounting

Known spend USD 1.6523; held USD 0.0000; available USD 2.3477. Complete: True; breach: False.

Inspect budget-status.json and dispatch-budget.json. Reconcile unresolved invocations with terminal provider evidence before reusing their allowance.
