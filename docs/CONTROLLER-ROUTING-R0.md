# Controller-aware routing R0 baseline and contracts

Date: 2026-09-18. Status: complete. Runtime policy: unchanged B0.

R0 turns the proposal's assumptions into a reviewable boundary before runtime
work begins. The machine-readable baseline is
[`test/results/2026-09-18-controller-routing-r0-baseline.json`](../test/results/2026-09-18-controller-routing-r0-baseline.json).
The proposed v1 contracts are
[`src/controller_routing_contracts.json`](../src/controller_routing_contracts.json).
They are not yet a production policy or a claim of measured Controller value.

## Reproduced baseline

The focused offline suite demonstrates four current behaviours:

1. `evaluation_live_worker.cell_identity()` rejects `worker-fable-low`.
2. `evaluation_runner.expected_model()` maps a Fable cell to Sonnet.
3. A `controller-stability` result of `stable=false` is recorded, then quick
   mode continues into Generate and returns a solution.
4. Quick mode chooses the first critique-passing generated candidate before
   calling Selector; a valid Selector result excluding it does not change the
   winner.

These are characterisations, not desired permanent assertions. R1 replaces
the two Controller-integrity behaviours. R2 replaces the two identity
behaviours through one shared model registry. The tests are renamed or revised
only in the stage that changes the corresponding behaviour, preserving the
pre-change evidence in this result and repository history.

The existing qualified-default regression independently proves that every
assessment still receives the B0 sequence: Sonnet-low, one Sonnet-low repair,
then Opus-high, with Controller disabled. The prior real-world campaign remains
valid evidence for B0 versus B1. It contained no live Controller episode and
therefore supplies no causal estimate of Controller benefit.

## Frozen v1 contracts

`src/controller_routing_contracts.json` fixes the semantic boundary used by
R1-R4:

- workflow selection (`worker` or `controller`) is separate from model/effort;
- operator/CLI intent wins, followed by task, session, project and shipped
  default; a narrower explicit `auto` overrides a wider `on` or `off`;
- changing a setting does not itself launch paid work, and repository content
  cannot manufacture an operator override;
- assessments distinguish consequence, premise uncertainty, alternatives,
  coupling, available verification, failure cause and evidence provenance;
- every decision records both the recommendation and effective overridden
  action, including qualification, reason, budget and next checkpoint;
- operator constraints and acceptance contracts remain external and immutable
  to Controller roles;
- a compact evidence packet can preserve checked progress from a gap, but a
  gap cannot claim completion and a dissolution needs independent checking;
- execution status, semantic quality, cost and latency remain separate.

The initial automatic trigger is deliberately narrow: a material, checkable
premise contradiction, or consequential/irreversible work that combines
unresolved assumptions with material alternatives or coupled constraints.
Reactive entry requires a new premise conflict or contradictory attempts about
the problem frame. Difficulty words, length, confidence, missing access,
infrastructure failure and an ordinary implementation defect are insufficient
alone. The initial limits are one Controller invocation and three worker
attempts per task revision.

## Historical freeze and rollout boundary

R1-R4 use the new policy ID `rigour-auto-v1`. They must not rewrite B0, its
reserved evidence digest or its historical replay path. Any candidate remains
experimental until the staged evaluation and installed-consumer gates pass.
R8 may promote `auto`; before then, all default behaviour remains B0.

No provider call was made in R0. The pre-change full offline harness passed
51/51 checks. The completed R0 harness passed 52/52, including `CTRL-R0`; its
focused suite passed all six contract and characterisation tests.
