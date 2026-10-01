# Prospective X5 task redesign brief

Date: 2026-09-28 Australia/Sydney. Status: **provider-free proposal**, not
a frozen campaign or permission to spend. The v1 and v3 screening failures
remain valid development evidence. The [candidate audit]
(controller-x5-public-candidate-audit-2026-09-28.md) found that current
actors announce their single faults in source comments, so merely adding
incident traces would not test whether Controller improves uncertain work.

## Task construction rule

Create four new X5-only development actors; leave X3 actors, variants,
protected oracles and reserved tasks byte-for-byte unchanged. Each actor
must have at least two plausible, materially different failure mechanisms
that fit the initial symptom. The public issue supplies an incident report,
observations and authorised outcome, but neither names the actual code fault
nor prescribes a complete patch. Source comments describe interfaces and
invariants without saying which path is defective. Public traces and the
baseline runner must reproduce the observations exactly. The alternative
causes need different probes and different safe repairs; generic prose
about "uncertainty" is insufficient.

| Case | Competing causes to make testable | Public evidence and independent acceptance |
| --- | --- | --- |
| Payment replay | A second purchase, a committed retry whose response was lost, or a replay record written out of step with the debit. | Same-tenant key and attempt timeline, response-loss event and balances. Hidden checks cover same-key replay, changed amount, tenant boundary, pre-commit abort and concurrent retry. Preserve at-most-once charge and truthful failure reporting. |
| Tenant feature leak | Backend routing, cache identity collision, or stale update/invalidation. | Cold and warm lookup traces with backend tenant, cache hit/miss and store events. Hidden checks distinguish cross-tenant isolation, per-feature separation, update replacement and unrelated entries. A patch that merely hides the sample value fails. |
| Lease-service lag | Database saturation, worker clock skew, or stale-owner acknowledgement after lease reassignment. | Queue lag, stable DB metrics, server/worker timestamps and lease ownership transitions. Hidden checks cover clocks ahead and behind, expiry boundary, fencing token, stale acknowledgement and input order. |
| Monetary discrepancy | Per-line rounding, binary-float aggregation, or refund sign handling. | Multiple ledger/statement examples with fractional cents and a separate approved policy contract for decimal final rounding. Hidden checks cover negative refunds, half-even ties, large totals and both consumers. The task must determine which mechanism explains each observation before repair. |

Use one unchanged ordinary worker control such as N01-D1 and one unchanged
missing-decision clarification control such as C08-D2. This preserves a
six-task screen with four proposed suitable tasks, rather than selecting
only cases that a prior assessor happened to route to Controller. A case
that fails the construction rule is excluded before any model assessment,
with the reason recorded. A second reviewer or deterministic audit checks
the public materials for answer leakage before the task list is frozen.

## Evidence and staged gates

1. Build each actor and its independent acceptance contract. Provider-free
   tests must reproduce the baseline symptom, discriminate at least two
   alternatives, accept the intended safe repair, reject a plausible wrong
   repair, reject a label-only report and reject a partial patch that falsely
   claims completion. Keep the hidden cases inaccessible to the actor.
2. Freeze actor files, trace bytes, acceptance/oracle bytes, source runtime,
   host identity, selection rubric, six task IDs, B/S/A pairing and stop
   rules before any public assessment. Preserve all v1-v3 attempts in the
   analysis; do not treat v4 as independent replication.
3. Run one public assessment per task under a fresh single-use root and
   USD 0.50 local cap. Require four actual automatic Controller admissions,
   worker for the ordinary control and clarification for the decision
   control. A miss stops before pilot role calls and is reported without
   relabeling the task or changing the threshold.
4. Only after that gate passes, run the matched 18-episode B/S/A pilot on
   the same frozen public inputs. Require equal task evidence and independent
   acceptance for each arm, count every attempt and role call, and measure
   provider-reported cost and wall time. Preserve partial work and failed
   receipts in the comparison.
5. Score useful incomplete work as well as completion: independently
   reproduced causal findings, probes that actually distinguish causes,
   preserved safety invariants and truthful next steps. Report acceptance,
   false success, critical errors and each partial-quality component
   separately; do not infer uplift from a Controller label or role count.
   Freeze the exact point weights and critical-error veto with the existing
   quality evaluator before the first paid call. Use blinded arm labels for
   any human adjudication.

The v3 Q4R Sonnet High canary may be reused only if installed launcher,
schema, provider identity, auth method and relevant source still match its
receipt. Otherwise require a new bounded canary. The screen's **USD 3**
local ceiling corresponds to about **USD 0.15-0.60 API-equivalent** based on
observed assessments. The later 18-episode pilot retains its **USD 144**
local ceiling and prior **USD 5-30 API-equivalent** projection; these are
separate spend notices, and local caps are not provider invoices. Allow
roughly **6-10 hours** to build and verify four fair actors, **1-2 hours**
for the screen and **2-8 hours** for the pilot. A favourable development
result would still require the separately frozen X6 reserved comparison and
X7 independent decision before any default promotion.
