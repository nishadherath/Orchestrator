# N5 to N6 decision preflight

Date: 2026-09-25. Scope: provider-free review of the **predeclared N6 gate**
after the completed [N5 development comparison](worker-n5.md). No N6 stage
has started. No reserved R actor was run, graded or inspected for this review.
The experimental N5 candidate remains frozen and B0 remains the shipping
default.

## Decision

**Recommendation: do not buy the planned 48-episode N6 comparison as a
promotion test.** Its predeclared 12-task bounds can pass only with an extreme
observed improvement, while N5 found no quality gain attributable to stronger
first-cell routing on the moderate and complex development tasks. The existing
N6 run could still describe performance on its reserved synthetic suite, but
it cannot credibly settle the intended economical routing decision for ordinary
real-world work. Preserve its sealed tasks and the frozen protocol. Any new
qualification campaign needs a separately versioned, operator-reviewed design
before its own reserved outcomes are viewed.

## Reproducible feasibility calculation

[Contract v2 section 10](../WORKER-EXECUTION-CONTRACT-v2.md) fixes 12
independent task mechanisms, with two repetitions per arm aggregated into one
task result. Its simultaneous gate uses a Clopper-Pearson net acceptance lower
bound and a Hoeffding quality lower bound. The implementation is
[worker_statistics.py](../../tools/worker_statistics.py). At `n=12`:

| Necessary observation | Value | Implication |
| :--- | ---: | :--- |
| Quality penalty `200 sqrt(log(40)/(2n))` | 78.4100 points | To make `L_Q > -5`, the observed mean candidate-minus-B0 quality must exceed **73.4100 points**. |
| Quality superiority path `L_Q > 5` | 83.4100-point gain needed | Even before the cost and safety gates. |
| Acceptance lower bound with zero candidate-only wins and zero B0-only wins | -0.3059 | Equal acceptance cannot pass the `>-0.05` floor. |
| Minimum candidate-only wins with zero B0-only wins | 8 of 12 | Any B0-only loss makes the needed win count at least nine; two losses make the gate unreachable at 12. |

The first quality floor implies B0's observed mean quality must be below
26.5900/100 even if the candidate scores 100/100 on every task. The quality
superiority path implies B0 below 16.5900/100. These are mathematical
consequences of the frozen bound, not predictions about the reserved tasks.
For comparison, N5 development B0 averaged 97.2225/100 and candidate
100/100; the sole development quality difference occurred on a routine task
where both policies start in the same cell. N5 observations are not a sample
from the reserved distribution and cannot be treated as R outcomes.

The calculation can be reproduced without provider calls or reserved data:

```text
python -c "import sys, math; sys.path.insert(0, 'tools'); import worker_statistics as w; n=12; p=200*math.sqrt(math.log(1/.025)/(2*n)); print(p, p-5, p+5, w.cp_lower(0,n)-w.cp_upper(0,n)); print(next(k for k in range(n+1) if w.cp_lower(k,n)-w.cp_upper(0,n)>-.05))"
```

It yields `78.41002756996855 73.41002756996855 83.41002756996855
-0.30592057947271034` and `8`. The existing N4 fixed-seed simulation also
found zero passes in its equal, modest and large illustrative scenarios;
those scenarios are illustrations, not measured power.

## Cost and options for operator review

The original N6 schedule is 12 R tasks, two arms and two repetitions, or
**48 episodes**. Its local admission allocation is **USD 144** at USD 3 per
episode. This is not a bill forecast or provider hard cap. The plan estimates
4-10 hours of live execution in addition to engineering time. N5's 36
development episodes reported USD 3.36177041 API-equivalent usage over about
98 minutes, but different tasks, repetition and cache behaviour make a simple
48/36 extrapolation unreliable. A concrete dated spend notice is still
required if the operator chooses to run N6.

1. **Recommended: defer the existing N6 spend and redesign qualification.**
   Specify harder, representative multi-file tasks, a defensible sampling
   frame, an attested actor boundary for those edits, and a prospective analysis
   with useful power at an affordable sample size. Use public pilot tasks to
   test difficulty and operational cost. Freeze new reserved tasks and the
   analysis before any new outcomes. Preserve N5 and existing R evidence as
   historical data, not as an excuse to choose a favourable method after
   viewing results. This requires an operator-approved change to the staged
   plan and a new cost notice before paid work. A first provider-free design
   checkpoint is estimated at 3-6 engineering hours; the corpus, host and
   eventual live-run costs need separate estimates once scope is frozen. The
   [redesign proposal](../WORKER-QUALIFICATION-REDESIGN-PROPOSAL-2026-09-25.md)
   and [Q0 design record](worker-q0.md) define the checkpoints and stop rules
   without starting a paid campaign.
2. **Run original N6 only as an exploratory synthetic-suite comparison.**
   Keep the existing frozen gate and report its likely inconclusive result
   honestly. It may reveal implementation or safety failures, but it should
   not be sold as a realistic path to qualifying the default. Requires the
   N6 stage direction and exact paid authorisation.
3. **Stop policy qualification and retain B0.** Continue with consumer
   integration only after amending N7/N8 dependencies and scope. This saves
   experimental spend but leaves broader task-sensitive routing unqualified.

The current [execution protocol](../REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md)
requires operator direction and review at each stage. Contract v2 explicitly
forbids retrospectively changing N6's bound after N5 spend under the same
campaign. This review therefore changes neither that contract nor the R
schedule. The exact next action is an operator decision among the options,
preferably the first; no paid call or model switch is needed to make it.
