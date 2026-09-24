# N3: public assessment and experimental worker selector

Date: 2026-09-24. Result: **offline implementation complete; shadow only**.
N4 has not started. The [worker-first plan](../WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md)
and [worker routing plan](../WORKER-ROUTING-ACTION-PLAN-2026-09-19.md)
govern this stage. The [consumer guide](../../src/WORKER-SELECTOR.md)
defines the API and limits.

## Delivered behaviour

- `tools/worker_selector.py` accepts only a structured public-fact assessment.
  It preserves evidence source, reference and claim, verification strength,
  required artefacts, context demand, deadline, failure cause and uncertainty.
  Unknown fields, hidden-source evidence and malformed values fail closed.
  Equivalent descriptions with the same structured facts produce the same
  evidence cohort and selection. No additional paid assessment or evidence
  lookup was added.
- The versioned `worker-shadow-v1` policy resolves each of the 15 registry
  model/effort cells. Every row reports host eligibility, qualification,
  availability, historical or unknown cost, deadline fit and explicit
  rejection reasons. It exposes alternatives that change effort and model
  without assuming either produces a monotonic quality or cost gain. Routine,
  moderate and complex task priors are Sonnet low, Sonnet high and Opus high,
  respectively; these are unqualified labels pending N5 evidence.
- Uncertain framing stops as `unresolved_frame` and never invokes Controller.
  Missing facts request clarification, context overflow requests
  decomposition, and infrastructure, permission, identity and accounting
  faults block host repair. One local implementation failure may receive a
  bounded repair; a second stops. A missing verifier stops selection.
- An explicit cell request includes actor, unique authority, reason and
  optional cost ceiling. Unsupported cells, absent host support, insufficient
  budget and unknown cost without a ceiling are rejected without substitution.
  Unknown wall time cannot satisfy a stated deadline. Cache reuse is unknown
  and never subtracted from projected cost.
- `TaskExecutor.shadow_select()` journals a candidate beside the frozen B0
  cell, without changing dispatch, root budget or attempt ceiling. A call
  already in flight keeps its model and effort. Its reserved allowance is not
  counted as free budget for a simultaneous override. The production adapter
  does not yet attest the full host cell/cap capability needed for a live
  selected candidate; N5 must screen that boundary before promotion.
- The redistributable includes the selector and its consumer guide. The
  isolated consumer smoke test imports and records a shadow override from a
  copied bundle while the B0 worker still runs its original cell.

## Offline evidence

The focused N3 suite passed **7/7** tests. It covers all 15 explicit cells,
requested CLI model and effort for each, equivalent wording, hidden-field
rejection, missing evidence, failure taxonomy, budget and host rejection,
cache uncertainty, override provenance, in-flight isolation and unchanged B0
dispatch. The existing N1 executor suite passed **38/38**. The checked
distribution build passed its offline gate. The copied-bundle consumer test
passed B0, managed delegation and N3 shadow selection without source-tree
imports. The post-build full harness returned **PASS** on all 58 checks,
including distribution parity and the 24-task real-world fixture suite. Its
release check had no mechanical failures; the initially dirty bundle stamp
is resolved by a clean source commit and rebuild. No paid worker,
Controller or evidence lookup was made.

## Limits and next gate

Structured public evidence still needs a trustworthy caller; the schema
cannot detect a hidden answer pasted into a claim string. Historical cost
table means are task-dependent and predate later price changes, so they are
uncertainty markers rather than current quotes or provider spending limits.
Fake command pinning proves requested effort, not served effort. Shadow
selection cannot improve task results until a later qualified dispatch policy
uses it. N4 must build independent evaluation and protected oracle isolation;
N5 must screen current host identity, availability, effort and spending.

Stop after N3 for operator review. Do not start N4 in this session.
