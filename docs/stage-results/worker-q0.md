# Q0: worker-routing qualification redesign

Date: 2026-09-25. Gate: **provider-free design complete for operator review;
Q1 and paid work have not started**. The [proposed protocol](../WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md)
is a new prospective programme. It does not amend the frozen N6 contract,
execute or inspect its R outcomes, promote a routing policy, or alter B0.
The worktree is on `v1.0-rc1` at HEAD `15ecf66`, with pre-existing N5 work
and this Q0 work uncommitted.

## Observed basis and design choice

The [N5 development record](worker-n5.md) has 12/12 hidden acceptance for its
experimental candidate but no quality gain attributable to changed routing
on moderate or complex tasks. The [N6 gate review](worker-n5-n6-gate-review-2026-09-25.md)
shows that its 12-task bound needs more than 73.41 observed quality points of
mean gain and at least eight candidate-only acceptance wins with no losses.
That comparison is not a cost-effective promotion test for plausible modest
effects. The existing R tasks remain sealed. Historical W07/W08 multi-file
fixtures and results in the [older real-world plan](../REAL-WORLD-EVALUATION-PLAN.md)
can reduce public pilot preparation; their known outcomes cannot become new
reserved evidence.

Q0 proposes one first-cell routing stratum: offline Python CLI/service
maintenance involving coordinated multi-file changes or stateful,
concurrency, protocol or diagnosis faults. The proposed 2-8-file and
1,000-20,000-line limits make the initial study reproducible and cost-bounded.
They limit its claim; they do not describe every task a redistributable
orchestrator may receive. One task per independent source project or authored
codebase family is the preferred statistical unit. Shared repositories,
templates or repeated episodes cannot inflate `n`.

The [protocol](../WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md) defines
public-feature admission, identical paired task materials/caps, independent
hidden acceptance, 0-100 quality that credits useful incomplete work,
critical-error and false-success tracking, model/effort and charge evidence,
and an explicit same-first-cell variance control. The first candidate and
the reserved task set are chosen only after public pilot evidence, then frozen
before reserved outcomes.

## Feasibility of a narrower superiority claim

Q0 proposes one predeclared stratum and two alternative directional paths:
hidden acceptance wins/losses, or material quality wins/losses defined by a
10-point task-level difference. Each uses a one-sided exact paired sign tail
at `p < .025`; Bonferroni across the two paths controls familywise false
positive probability at at most .05 under independent, exchangeable task
units. An acceptance path also needs at least 15 percentage points observed
net gain; the quality path needs at least 10/100 observed mean gain. These
thresholds are proposed engineering values, not measured user utility.
Safety and cost guards can only make the full gate harder to pass.

The [exact power tool](../../tools/worker_qualification_power.py) enumerates
win/loss/tie task outcomes. Its inputs below are **hypothetical probabilities**,
not estimated worker performance. Values are marginal probability that one
directional test rejects at .025; they are upper bounds on the probability
that every quality, safety and economic guard passes.

| Independent tasks | Modest 20% wins / 10% losses | Useful 35% / 10% | Strong 45% / 5% | One-sided 95% upper adverse rate after zero events |
| ---: | ---: | ---: | ---: | ---: |
| 12 | 0.9% | 9.6% | 32.0% | 22.09% |
| 24 | 6.5% | 33.9% | 79.9% | 11.73% |
| 36 | 11.6% | 54.8% | 95.4% | 7.98% |
| 48 | 16.9% | 69.5% | 99.0% | 6.05% |
| 60 | 22.1% | 80.1% | 99.8% | 4.87% |

Thus 24 independent tasks are a sensible **strong-effect screen**, not a
modest-effect qualification. Around 60 would be needed for 80% marginal
power under the illustrative 35%/10% win/loss scenario, before other gates.
Even zero critical errors in 24 tasks cannot show a population risk below
1%; the exact one-sided 95% zero-event bound crosses 1% only at 299
independent tasks. Q0 therefore recommends a positive 24-task result support
at most a limited, monitored opt-in after review, not broad default
promotion. If the operator requires a general five-point non-inferiority or
sub-1% safety claim before any use, this design is a **no-go at the proposed
small sample** and needs a separately costed larger study.

The table is reproducible, for example:

```text
python tools/worker_qualification_power.py --tasks 24 --win-probability 0.45 --loss-probability 0.05 --alpha 0.025
```

The exact paired-sign method is documented by [NIST for McNemar](https://itl.nist.gov/div898/software/dataplot/refman1/auxillar/mcnemar.htm)
and [NIST for the sign test](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/signtest.htm).
Exchangeability and a defensible task frame are assumptions to validate in
Q2/Q4, not facts inferred from a curated suite. A conditional sign test is
evidence about directional wins among discordant tasks; it is not a
confidence interval for a small mean gain.

## Cost and sequence

N5's 36 single-file development episodes reported USD 3.36177041 in
API-equivalent receipts, or about USD 0.0934 per episode, over about 98
elapsed minutes. Multi-file work is likely more expensive, but its ratio is
unmeasured. For planning only, Q0 uses **USD 0.10, 0.50 and 2.00 per
episode** as 1x, about 5x and about 21x N5-scale scenarios. These are
workload assumptions, not the price of any model or a subscription bill.
The [Anthropic pricing page](https://platform.claude.com/docs/en/about-claude/pricing)
was checked on 2026-09-25; Q3 must reprice the actual served model, input,
output and cache mix. The page lists newer models that this project's
current host capability has not attested, so Q0 makes no availability claim.

| Reserved design | Episodes | API-equivalent scenario, USD | Local allocation if USD 3/episode | Serial call-time scenario at 3-15 min/episode |
| :--- | ---: | :--- | ---: | :--- |
| 24 tasks, one run per arm | 48 | 4.80 / 24 / 96 | 144 | 2.4-12 h |
| 24 tasks, two runs per arm | 96 | 9.60 / 48 / 192 | 288 | 4.8-24 h |
| 60 tasks, one run per arm | 120 | 12 / 60 / 240 | 360 | 6-30 h |
| 60 tasks, two runs per arm | 240 | 24 / 120 / 480 | 720 | 12-60 h |

The first public pilot tranche is **eight B0 episodes**, roughly USD
0.80-16 under the same scenario and USD 24 local admission allocation if
the prior USD 3 cap proves sufficient. Up to eight B0 repeats and up to
eight candidate episodes require separate predeclared gates; all 24 would
be USD 2.40-48 scenario usage and USD 72 local allocation. A local cap is
not a provider hard stop, and harder tasks may require a different cap.
No such spend is authorised by Q0.

Planning engineering effort, independent of API usage: Q1 multi-file boundary
8-16 hours; Q2 public pilot preparation 4-8; Q3 pilot design/reconciliation
2-4 plus live time; Q4 authoring and validating 24 genuinely independent
reserved tasks roughly 24-60; Q5 runner/analysis 2-4 plus live time; Q6
adjudication 2-4. These ranges are low-confidence judgment, not measured
work logs. **Fixture authoring and validation may dominate API spend.** The
cost-sensitive sequence therefore reuses known tasks as public pilot material
and delays reserved corpus construction until the pilot shows a plausible
large, attributable gain. Q3 must publish an exact dated spend notice and
stop if the prospective value of information is too low.

## Exit and next gate

Q0 has produced a target frame, one candidate-stratum strategy, material
effect thresholds, a reproducible exact directional analysis, power and
safety limits, and a priced staged go/no-go. It has not proved that suitable
independent repositories exist, that multi-file WSL isolation works, that
any stronger cell improves quality, or that the operator values a particular
USD premium. Those are Q1-Q4 questions, not assumed Q0 outcomes.

Verification on the normal host: `python test/harness/check.py` passed **63/63
checks**, including the new `WORKER-Q0-POWER` entry; the focused power suite
passed three tests, Python compilation passed, and `git diff --check` was
clean. A fixed-seed 100,000-trial independent simulation gave 80.12% for the
strong 24-task example versus the exact 79.94%, a numerical cross-check rather
than evidence about worker quality. The local Markdown links resolve.
The N5 development reconciliation still passed: 36 episodes, 50 calls and
USD 3.36177041 provider-reported API-equivalent usage. `release_check.py`
found all 75 distributed files source-equivalent and no sensitive material;
its clean stamp and publication actions remain open because the branch is
dirty and publication is an operator action. No consumer `src/` file changed
in Q0, so `dist/` was not regenerated.
After the final documentation edits, the targeted prose check still passed
for all 618 authored files and `git diff --check` remained clean.

An initial restricted-sandbox harness run failed three pre-existing fixture
checks, including an explicit child-process permission denial. The first
normal-host retry stopped at the old 240-second timeout for the N5 fake-screen
suite. That suite passed alone in 205 seconds and took 287 seconds within the
full gate. The harness timeout for that one suite was raised to 420 seconds;
the final normal-host full gate then passed. No Claude worker, Controller or
DeepSeek semantic-summary call was requested by Q0 tooling; no served
model/effort identity is claimed for this design checkpoint.
Graft's provider-free structural build indexed the changed Q0 Python files
(2,992 nodes, 6,709 edges). Its semantic freshness check still reports
unbuilt Q0 summaries and the previously failing `TaskExecutor` summaries.
The DeepSeek-backed deep refresh failed twice before Q0 with an unparseable
tool-call response; Q0 did not repeat that paid failure path. Exact prior
DeepSeek usage and charge remain unknown.

**Recommendation:** approve Q1 as the next provider-free boundary stage and
the revised Q2/Q3 pilot-first order. Retain B0 and leave the original N6
R tasks untouched. Review the proposed 15-point acceptance, 10-point quality
and provisional cost guardrails before Q4 freezes a reserved campaign.
Stop here for the project protocol's Q0 operator review.
