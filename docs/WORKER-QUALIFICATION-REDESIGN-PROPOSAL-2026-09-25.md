# Proposal: decision-useful worker routing qualification

Status: **Q0-Q2 provider-free stages complete for review; no Q3 paid campaign authorised**. Date:
2026-09-25. This does not start N6, alter the frozen worker-execution
contract, inspect the reserved R outcomes or authorise paid calls. It follows
the [N5-to-N6 gate review](stage-results/worker-n5-n6-gate-review-2026-09-25.md)
and is detailed in the [Q0 protocol](WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md).

## Decision to be tested

The production question is whether an observable public task feature should
change the worker's first model/effort cell, after counting every assessment,
attempt, repair and verification charge. The current default B0 is the
comparator. A rule may be qualified for a **specified task stratum** and leave
B0 elsewhere; a suite result must not be described as a population-wide
non-inferiority result without an appropriate sample and interval.

Success needs independent hidden acceptance, useful partial quality even
when incomplete, critical-error and false-success rates, all-attempt cost,
and elapsed time. The candidate must also demonstrate that its gain is caused
by a changed routing decision rather than stochastic variation between arms
that choose the same cell. N5's routine difference failed that attribution
test. Unavailable cells, unknown charges and served-effort uncertainty remain
separate from quality outcomes.

## Conditional staged work

| Checkpoint | Work and output | Paid calls | Stop condition |
| :--- | :--- | :--- | :--- |
| Q0, protocol and economics | Define target task distribution, candidate strata, minimum worthwhile quality/cost effect, analysis method and prospective sample-size/power or decision-loss calculation. Publish a versioned protocol and priced go/no-go. | None | No affordable design can distinguish the minimum worthwhile effect. |
| Q1, multi-file boundary | [Completed provider-free](stage-results/worker-q1.md): a versioned manifest-bound path set passed 38 WSL boundary and five budget checks, with the old single-file transport retested. Multi-file grading and a paid adapter remain Q2/Q3 work. | None | Any evaluator exposure or unaccounted write. |
| Q2, public pilot preparation | [Completed provider-free](stage-results/worker-q2.md): two pinned public upstream families fit the stratum; six isolated baseline/partial/reference grades separate useful progress. The [Q2 protocol](WORKER-QUALIFICATION-PROTOCOL-Q2-2026-09-25.md) freezes prospective source/issue selection. Historical D/H fixtures are too small to count as target tasks. | None | Public examples cannot exercise the proposed stratum or run reproducibly. |
| Q3, public pilot | Review a proposed two-task B0 canary first; it measures difficulty and cost but cannot invoke the original eight-task ceiling/floor thresholds. Curate six more independent public families before applying that gate. Only buy candidate episodes when the prospective information gain justifies them. | Separately priced and authorised | Grader ambiguity, cost overrun, insufficient model identity evidence or no useful task difficulty. |
| Q4, reserved corpus and policy go!freeze | Only after the public pilot, curate pinned redistributable open-source issue snapshots where feasible, plus independently authored synthetic cases for controlled failures. Freeze licences, commits, setup, dependencies, public checks, independent hidden oracles, candidate, schedule, analysis, cap and stop rules before any reserved outcome. | None | Tasks cannot be reproduced or graded independently, or the projected qualification cost exceeds the operator's value or limit. |
| Q5, reserved comparison | Pair B0 and candidate on genuinely unseen tasks, randomise arm order within task, preserve task as the independent unit, account for repeated attempts and cache effects, reconcile every call and grade after writer stop. | New exact notice and authorisation | Integrity fault or predeclared futility/safety stop. |
| Q6, independent adjudication | Review outputs, leakage, sampling claims, effect attribution and economic decision. Promote only a supported stratum with operator direction; otherwise retain B0 and report the negative result. | None unless a separately approved reproduction is necessary | Evidence cannot support the proposed production claim. |

Q0 through Q2 are complete as provider-free checkpoints. Q3-Q6 need their own
estimates and operator review; the [Q0 result](stage-results/worker-q0.md)
gives planning envelopes, not paid authorisation.
The existing N6 allocation of USD 144 is not transferred to this proposal.
The completed N5 spend and the reserved synthetic R suite remain historical
evidence; neither is silently reclassified as fresh held-out data.

## Cost-sensitive design rules

1. Spend first on public B0 difficulty and grader calibration. A task that
   nearly every B0 run solves cannot measure a stronger first cell's quality
   benefit; a task nobody can solve may only measure partial progress.
2. Prefer deterministic, standard-library fixtures when they faithfully
   model the failure. Use pinned open-source snapshots for the integration
   behaviour synthetic fixtures cannot represent. Record licences and exact
   source commits before packaging anything for redistribution.
3. Freeze the target distribution before selecting successful examples.
   Stratify on public attributes such as repository size, edit breadth,
   diagnosis uncertainty, concurrency and destructive-action risk. Do not
   expose evaluator labels or outcomes to the router.
4. Compare a changed route with B0 on the same task. Explicitly separate
   model effects, effort effects and repair-policy effects. A same-cell pair
   is a variance control, not evidence for a selector benefit.
5. Predeclare an analysis whose confidence or decision threshold can be
   reached at the proposed sample size under a plausible worthwhile effect.
   Report sensitivity to the task sampling frame. If the affordable sample
   supports only suite-scoped evidence, say so and require monitored rollout
   rather than claiming broad qualification.
6. Keep admission allocations, provider-reported API-equivalent receipts and
   actual subscription billing distinct. Reserve before each side effect;
   stop on uncertain accounting and never replay an ambiguous call.

The [execution protocol](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md) still
requires operator direction at stage boundaries. The original N6 contract
continues unchanged unless the operator chooses a new, prospectively reviewed
programme. This document is the concrete scope for the first decision, not an
approval to implement or spend.
