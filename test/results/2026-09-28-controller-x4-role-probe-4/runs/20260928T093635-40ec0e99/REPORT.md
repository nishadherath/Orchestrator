# Controller report, 20260928T093635-40ec0e99

Outcome: gap. Mode: quick. Calls: 17. Cost: USD 3.2275. Ledger frozen at v2.

## No solution

Termination: no_improvement.
Next cheapest test: Verify or replace every ineligible candidate premise.

## Acceptance criteria

- Each of the three competing explanations has at least one check that names an observable artefact and states the outcome pattern that confirms it while disconfirming the other two.
- Exactly one containment step is proposed, with its reversal stated and its effect on the pending diagnosis noted, including any evidence it would destroy.
- The implementation direction is stated conditionally, naming the specific check result that would authorise it.
- No check is described as having been run; every result is prospective.
- Only the supplied statement is used; no system detail, tool, log name or metric is asserted as existing without being flagged as an assumption.
- Load-bearing unverified premises are named, including the assumption that the cause lies among the three listed explanations.

## Premise ledger

Every premise at the frozen version, with the class verification left it in.

- prem-002 [unverified, confidence 0.85]: Acknowledging a job to the queue and writing its receipt are two distinct operations against two distinct stores, performed by the same service.
- prem-003 [unverified, confidence 0.8]: At least one job has been acknowledged with no corresponding receipt present in the receipt store. This is reported, not measured in this run.
- prem-004 [law, confidence 0.9]: Without an atomic commit, outbox or equivalent protocol spanning both stores, an acknowledgement can durably succeed while the receipt write does not, so acknowledgement-without-receipt is possible by construction.
- prem-005 [unverified, confidence 0.5]: The cause lies among exactly three explanations: the writer failed, the acknowledgement was premature, or an idempotency check suppressed a legitimate retry. This closed-world assumption is stated, not established.
- prem-006 [unverified, confidence 0.7]: Jobs can be redelivered and retried, and an idempotency check sits on the retry path with the power to suppress a receipt write that should have occurred.
- prem-008 [unverified, confidence 0.5]: Evidence capable of separating the three explanations exists or can be obtained: writer error records, the ordering of acknowledgement against first write attempt, idempotency-key hit counts, and a job identifier shared by both stores.
- prem-009 [policy, confidence 0.95]: Only the supplied statement may be used as evidence. No repository, external system, prior fixture or assumed implementation detail may be introduced as fact.
- prem-010 [policy, confidence 0.95]: No proposed check may be described as having been run, and no result may be reported for it. Every check is prospective.
- prem-011 [policy, confidence 0.9]: The containment step must be reversible, meaning it can be undone without residue while the cause is still undetermined.
- prem-012 [policy, confidence 0.95]: The deliverable is an investigation brief with no production-change authority, and the implementation direction stays conditional until a check resolves the cause.
- prem-013 [verified, confidence 0.95]: The service is a synthetic fixture with no production system and no customer data behind it, so containment and diagnostic actions carry no external blast radius.
- prem-014 [verified, confidence 0.95]: The available notes do not discriminate among the three explanations, so the cause is currently unknown rather than merely unstated.

## Unverified load-bearing premises

- prem-002: Acknowledging a job to the queue and writing its receipt are two distinct operations against two distinct stores, performed by the same service. (cheapest verification: Read the service's job-completion path and confirm the acknowledgement call and the receipt write target different systems.)
- prem-003: At least one job has been acknowledged with no corresponding receipt present in the receipt store. This is reported, not measured in this run. (cheapest verification: Join acknowledged job ids to receipt-store keys over a fixed window and count unmatched acknowledgements.)
- prem-005: The cause lies among exactly three explanations: the writer failed, the acknowledgement was premature, or an idempotency check suppressed a legitimate retry. This closed-world assumption is stated, not established. (cheapest verification: Enumerate every path that acknowledges a job or skips a receipt write, and look for a fourth cause such as receipt deletion, key mismatch or read-replica lag.)
- prem-006: Jobs can be redelivered and retried, and an idempotency check sits on the retry path with the power to suppress a receipt write that should have occurred. (cheapest verification: Locate the idempotency key derivation and the branch it guards, and confirm it can skip a write on a redelivered job.)
- prem-008: Evidence capable of separating the three explanations exists or can be obtained: writer error records, the ordering of acknowledgement against first write attempt, idempotency-key hit counts, and a job identifier shared by both stores. (cheapest verification: Confirm the service emits writer errors, timestamps both operations, and carries one job id into the receipt store.)

## Ranked alternatives

- 1. cand-001 (b0, score 1.0): Baseline. Passed critique (crit-005 notes only fixture-scoping and ordering weaknesses, not disqualifying). All three challengers were returned by critique, so B0 stands as the only entry meeting acceptance criteria.
- excluded: cand-003 (rejected_by_critic)
- excluded: cand-004 (rejected_by_critic)
- excluded: cand-005 (rejected_by_critic)

## Audit trail

(none)

## Dispatch accounting

Known spend USD 3.2275; held USD 0.0000; available USD 2.7725. Complete: True; breach: False.

Inspect budget-status.json and dispatch-budget.json. Reconcile unresolved invocations with terminal provider evidence before reusing their allowance.
