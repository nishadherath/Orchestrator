# Q0 proposed worker-routing qualification protocol

Later status: the [Q3 eight-family public B0 gate](stage-results/worker-q3-public-2026-09-25.md)
completed under the operator's standing approval through Q4. The Q3 candidate
decision and Q4 freeze remain open. The status and proposed admissions below
record the original prospective design, not today's authorisation state.

The later [Q3 contract audit](stage-results/worker-q3-contract-audit-2026-09-25.md)
identified measurement and first-cell attribution gaps. Follow the
[implementation amendment](WORKER-Q4-MEASUREMENT-AND-FREEZE-2026-09-25.md)
before further paid screening or Q4 freeze; the statistical thresholds here
remain unchanged. No candidate or reserved schedule is yet frozen.

Status at proposal: **Q0 design proposed; Q1 and Q2 provider-free gates passed; no Q3 paid campaign authorised**. Date:
2026-09-25. This is a new prospective design. It does not amend the frozen
[worker execution contract v2](WORKER-EXECUTION-CONTRACT-v2.md) or repurpose
the existing N6 R tasks. B0 remains the production default. The
[Q0 stage result](stage-results/worker-q0.md) gives the feasibility and cost
calculations behind this proposal.

## Decision scope and sampling frame

The first claim is deliberately narrow: task-sensitive first-cell routing for
**offline Python service and CLI maintenance** that needs coordinated edits
across 2-8 files or diagnosis of a stateful, protocol or concurrency fault.
The proposed repository size is 1,000-20,000 source lines, with deterministic
local setup and no live external service or secret. These are operational
limits to keep the first study reproducible and affordable, not a description
of all real user work. Cloud deployment, visual UI, mobile, other languages,
unbounded context and experimental Controller tasks are outside this claim.

Before task outcomes are seen, Q2 must define a reproducible selection rule
for source projects and issue mechanisms. Prefer pinned permissively licensed
open-source snapshots with authored consumer regressions and offline tests.
Use independently authored synthetic repositories where a controlled failure
is otherwise impractical. Record licence, source commit, dependency lock,
setup command, issue origin and whether the fault is authored or upstream.
One task per independent source project or synthetic codebase family is the
preferred sampling unit. If several tasks share a project/template, analyse
that cluster as one independent unit or reduce the effective sample size.
Do not count repeated runs, variants or sibling issues as new task units.

Public task attributes may identify the target stratum: cross-module contract
change, state/recovery invariant, concurrency/protocol boundary, or evidence
that conflicts with the issue's diagnosis. No hidden grader result, corpus
family label, task ID or reference patch may enter assessment or selection.
The candidate may abstain and use B0. Selection coverage and abstentions count
in the intent-to-route analysis; report outcomes for changed-cell tasks
separately without treating that post-selection subset as the primary sample.
At most one primary stratum and one candidate policy may be frozen for a
reserved comparison. Additional strata or cells are exploratory and require
a new prospective familywise error allocation before a claim.
This is worker-only routing; no experimental Controller path is admitted.

## Outcome and attribution contract

Each arm receives the same issue, starting repository, public tests,
acceptance contract, tool boundary, root monetary cap and allowed repairs.
Balance arm order by task and record cache state. A task's two scheduled
repetitions, if required by the public pilot's variability check, are
aggregated before analysis. A task is hidden-accepted only if both repetitions
pass; its quality is the mean of both independent 0-100 grades. With one
repetition, use its single grade. Missing/failed episodes count as not
accepted and retain available partial quality; an invalid grader makes the
comparison inconclusive. This repetition choice must be frozen before any
reserved outcome.

Quality includes executable progress, preserved invariants, diagnosis,
clarification and truthful reporting even when the final task is incomplete.
Critical errors and false success are separate flags. Reference and materially
different correct variants must pass; public-answer copies, prohibited edits,
confident false completion and hidden-oracle access must fail. Grading occurs
only after the actor has stopped, outside its filesystem and Graft index.

Record first selected cell, requested effort, served model identity, effort
evidence or its absence, every attempt, wall time, cache counters and actual
provider-reported cost. Distinguish a policy benefit from run variation:
report pairs that selected the same first cell as a variance control. A
quality difference in that subset cannot by itself establish a selector
benefit. Compare changed first cells at a common repair ladder and cap.

## Prospective statistical and economic decision

The proposed minimum worthwhile effect within the **named stratum** is an
observed net hidden-acceptance gain of at least **15 percentage points** or an
observed mean quality gain of at least **10/100 points**, counting incomplete
work. These are engineering decision thresholds, not an estimate of user
willingness to pay. The one-sided primary directional tests are:

1. Acceptance: among task units where only one arm is hidden-accepted, use
   the exact paired binomial/McNemar tail for candidate-only wins against
   B0-only losses.
2. Material quality: classify each task's candidate-minus-B0 quality as a
   win at +10 points or more, a loss at -10 or less, and otherwise a tie.
   Use the same exact conditional sign tail for wins against losses. This
   path explicitly credits useful partial improvement.

Either path may support **stratum-scoped directional superiority** only if
its one-sided `p < .025` and its corresponding minimum worthwhile point
effect both hold. The two paths' Bonferroni allocation controls their
familywise false-positive probability at no more than .05 under the stated
independent, exchangeable task-frame assumptions. Ties remain in the task
denominator for point effects. Report exact win/loss/tie counts and both
p-values, even when the rule fails. The conditional sign test addresses the
direction among discordant tasks; it does not estimate a five-point
population non-inferiority bound or prove a particular mean effect.

The primary safety/economic guards are zero observed candidate critical
errors, no increase in false-success count, and no negative observed net
acceptance on the quality path or negative mean quality on the acceptance
path. Every actual or uncertain charge counts. Reject an option dominated
by B0 in observed quality and cost. Report incremental USD per additional
hidden acceptance and per ten total quality points, with undefined rather
than zero when the denominator is non-positive. Q3 must measure costs and
propose an explicit maximum premium and cap for operator approval **before**
the reserved schedule is frozen; do not infer willingness to pay from token
prices. The provisional planning envelope is at most 1.5 times B0's total
API-equivalent cost and USD 1 additional per triggered task. These are
proposed guardrails, not a bill prediction or final authority.

A positive 24-task result would justify at most a limited, monitored opt-in
for this stratum after independent review and operator direction. It does
not qualify a broad default: with zero adverse events in 24 independent
tasks, the one-sided exact 95% upper risk bound is still 11.73%. A default
change needs a separately approved evidence and rollout gate, with its
target population and acceptable safety risk stated prospectively. A
negative/inconclusive result retains B0 without changing thresholds or
replaying tasks. No candidate is promoted solely by a passing test.

## Staged admission and futility gates

1. **Q1, boundary:** [completed](stage-results/worker-q1.md) provider-free
   attestation of manifest-bound existing-file edits, actor-only Graft, no
   evaluator leakage, writer stop, collection and root accounting in WSL.
   The paid adapter and multi-file grader are separate later gates.
2. **Q2, public pilot material:** [completed](stage-results/worker-q2.md).
   Two pinned open-source families carry authored multi-file regressions;
   hidden baseline/partial/reference grades discriminate progress. The
   [Q2 protocol](WORKER-QUALIFICATION-PROTOCOL-Q2-2026-09-25.md) defines
   prospective reserved selection. Historical D/H fixtures were too small
   for the target stratum and never become new holdout evidence.
3. **Q3, bounded public pilot:** start with eight B0 episodes on public tasks.
   If more than six hidden-accept, the stratum has a ceiling problem; stop
   and revise the public task frame before new holdout construction. If fewer
   than two hidden-accept, verify that hidden partial scores distinguish
   credible progress and that stronger routes are feasible before proceeding.
   Use up to eight predeclared B0 repeats to measure run variation. Then run
   a small, predeclared candidate screen only if B0 difficulty and the
   prospective cost of information justify it. A changed model lineup needs
   new host identity evidence; no silent substitution. Compare raising Sonnet
   effort with changing to Opus or Fable on the same public task and cap when
   host support and cost permit. N5 already screened all 15 model/effort
   cells; Q3 need not rerun every cell on every task or force an expensive
   cell into the policy simply to report coverage.
   **Q2 admission finding:** only two independent public families are ready.
   A separately approved two-task B0 canary is proposed for difficulty and
   cost calibration; it is diagnostic and cannot invoke the eight-task
   ceiling/floor thresholds. Applying the original gate needs six more
   independent public families and a new exact paid approval.
4. **Q4, corpus and policy freeze:** build reserved tasks from the Q2 frame
   only after the pilot gate. Validate reference and alternative solutions,
   attack variants, actor isolation and licence provenance. Freeze the single
   stratum, candidate, sample size, repetition count, exact analysis,
   task order, caps and stop rules. The public pilot is excluded from
   reserved inference. Recalculate sample-size and cost feasibility before
   any reserved dispatch.
5. **Q5, reserved comparison:** run only with a new exact operator-approved
   manifest and dated spend notice. A terminal failure or uncertain receipt
   never becomes an automatic replay. Preserve all partial grades and
   charges. Stop on an integrity fault or predeclared economic/safety futility.
6. **Q6, adjudication:** independently inspect actual patches and grades,
   task/project independence, cell attribution, effect and total cost.
   Decide opt-in, further evidence, or B0 retention. Default promotion is a
   separate operator decision with additional evidence.

The original N6 schedule, thresholds and R outcomes remain sealed. This
proposal is not a retrospective reanalysis of that campaign. The exact
binomial machinery follows [NIST's paired McNemar reference](https://itl.nist.gov/div898/software/dataplot/refman1/auxillar/mcnemar.htm)
and [sign-test reference](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/signtest.htm).
The implementation and hypothetical power calculations are in
[worker_qualification_power.py](../tools/worker_qualification_power.py).
