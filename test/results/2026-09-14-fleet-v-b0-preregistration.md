# Pre-registration: fleet versus B0, quick mode, 2026-09-14

Written before any fleet run on a benchmark task, per `docs/PLAN.md` Stage
11.1. Committed at the commit that carries it; the runs are scored against
this text as committed, and nothing here is revised after a result is seen.
Design and rationale: D55. Numbers: `docs/DECISIONS.md` D47 (B0), the
Stage 10 toy runs (`test/results/2026-09-14-system-controller-*.md` and
`runs/<id>/budget.jsonl` in `orchestrator-scratch`), and E24 (per-role cost).

## What is measured

Fleet arm: `tools/system_controller.py` quick mode against the task's
working copy, then `REPORT.md` handed with a fixed instruction and the
task's own handover to one `worker-sonnet-low` through `benchmark.py`'s
forwarder path, then `grade.sh`. Harness: `test/harness/fleet_benchmark.py`.
Controller inputs sha256 `3e356e82f2406f3b`; instruction sha256
`e92307fa1870e5af` (both printed by `--dry-run` at this commit; the harness
refuses to resume a checkpoint if either changes).

B0 arm: already measured, Stage 9.8, `worker-sonnet-low` with
`src/System/B0_BRIEF.md` prepended to the same handover, same forwarder,
same grader, twelve runs per task (three search, nine confirmation), T10
twice.

| Task | B0 passes | B0 confirmation | B0 mean cost per run | B0 cost per solved task |
| --- | --- | --- | --- | --- |
| T9 | 12 of 12 | 9 of 9, clears the bar | USD 0.3612 | USD 0.3612 |
| T10 | 22 of 24 | 8 of 9 and 8 of 9, does not clear | USD 0.3749 | USD 0.4090 |
| T11 | 12 of 12 | 9 of 9, clears the bar | USD 0.3515 | USD 0.3515 |

The reporting bar is nine runs with a 95 percent Wilson lower bound above
0.7, which at n = 9 only 9 of 9 clears (D15).

## The decision rule, from Gate A (D38), criterion 2

"On that set, the fleet in quick mode beats B0 at the reporting bar, at a
cost per solved task no more than three times B0's." The set is the tasks
where the floor fails the bar and a higher cell clears it: T10 (D42). So
the verdict is **system** only if both hold on T10:

1. the fleet passes 9 of 9 (B0's record is 8 of 9, twice; the fleet must
   clear the bar B0 failed), and
2. the fleet's cost per solved task, Controller plus instantiation, is at
   most 3 x USD 0.4090 = **USD 1.227**.

Otherwise the verdict is **prompt**, and Stage 12 wires the B0 brief in.
T9 and T11 cannot be beaten (B0 is 9 of 9 on both); they measure whether
the fleet regresses tasks the floor already clears, which only matters if
the fleet is going to be wired in.

## Predictions

P1. **Cost per fleet run: USD 2.3** (range 2.0 to 2.7). Controller USD
1.9 (three completed toy runs on T10's shape: 1.97, 1.87, 1.95; two to
three Framer calls at opus/high are half of it) plus instantiation USD
0.4 (B0's floor cost per run, since the report is about the brief's
length). D47's expectation of 1.0 to 1.5 is superseded by the measured
toy runs.

P2. **Criterion 2's cost clause fails regardless of the pass rate.** At
9 of 9 the fleet's cost per solved task equals its cost per run, USD 2.3,
1.9 times the ceiling of USD 1.227 and 5.6 times B0's. No pass rate can
bring it under the ceiling; that would need a Controller run under USD
0.83 in total.

P3. **T10 pass rate: 4 of 9** (plausible range 2 to 7; probability of 9
of 9 under 10 percent). Mechanism, from the toy runs: T10's grader
requires `normalise()` itself to strip, so the only fleet answer that
passes is the candidate that edits the frozen file, and the quick-mode
stop rule returns B0 ("honour the freeze") whenever every candidate that
survives critique carries an `unverified` introduced premise. In the
three completed toy runs the winner would have passed the grader once
(subtract, run 6) and failed twice (B0, runs 4 and 5); the run 5 subtract
candidate lost only on the class its generator gave one premise. Each
fleet pass therefore needs the subtract or re-represent generator to
survive critique without labelling "no consumer outside `downstream.py`"
as unverified, and the Critic (opus/medium, blind) not to return it. The
Verifier's one tool call falsifies the freeze's stated reason in every
toy run so far; that part is not in doubt.

P4. **Verdict: prompt.** P2 alone decides it; P3 is predicted to fail
too. If P3 is falsified by a 9 of 9, the verdict is still prompt on cost
and the entry says so in those words: the fleet did what `SYSTEM.md`
claims and did not pay for itself at this configuration.

P5. **Technique of the winning candidate on a passing run: subtract**
(the freeze premise is removed on the falsified justification). Logged
per run as the training signal `SYSTEM.md` section 8 asks for.

P6. **T9 and T11, if run: 7 to 9 of 9 each**, with failures, if any, from
the instantiating worker applying a paper answer that omitted a detail the
task's grader checks (T9's timing budget, T11's scale), not from the
Controller choosing wrongly. Cost per run as P1.

## Failure shapes and predicted rates, per nine runs

| Shape | Predicted | How it is recognised |
| --- | --- | --- |
| Forwarder confabulation at instantiation (D20: one turn, no tool use, invented prior exchange) | 0 to 1 | `instantiate.extras` shows `num_turns` 1 and seconds of duration; the run is void, not a fail, and is re-run once |
| Scribe rejections inside a Controller run | 1 to 3 per run, all recovered by the one-shot retry | `runs/<id>/rejections.jsonl`; a phase left with zero records after retry is a Controller failure, counted below |
| Controller failure (crash, or a phase with no valid record) | 0 to 1 | `error` starts with `controller:`; counted as a fail, since the fleet produced nothing to instantiate |
| Budget exhaustion (USD 3.0 per run) | 0 | outcome `gap`, termination `budget_spent`; mean toy cost is 1.9 with no run above 2.0 |
| A role editing the working copy before instantiation | 0 | `role_edits` non-empty in the run record; the run is flagged and excluded from the pass rate |
| Dangling reference in the ledger (D52's known limitation) | 1 to 2 runs | `validate_records.py` on the run's ledger; recorded, not a fail |
| Instantiating worker declines to apply the answer ("cannot be applied as written") | 0 to 1 | its report says so and the grader fails; counted as a fail, because the report was not actionable |

## Run plan

Sequential, cheapest question first, so a **prompt** verdict costs one
task's runs rather than three:

1. Pilot, one T10 run: plumbing only. If it runs end to end (Controller
   completes, worker edits, grader executes), it is run 1 of 9 and nothing
   changes. If a harness or Controller defect stops it, the fix is a
   decision entry, the checkpoint is archived with `--fresh`, and the nine
   start over; a pilot's pass or fail never changes the instruction or
   the configuration.
2. T10 to nine runs (eight more), about USD 21 in total for the nine.
3. T9 and T11, nine each, only if T10 came in at 9 of 9 and a system
   verdict is still arithmetically possible on cost; otherwise skipped
   and recorded as skipped under this rule. About USD 41 if run.

Total: about USD 21 in the predicted branch, about USD 62 if all three
tasks run. The plan's Stage 11 estimate was USD 15 to 55.

## Scoring

Each prediction is scored held or falsified in the verdict entry, with the
measured number beside it. P1 holds if the mean cost per run over the nine
T10 runs is within the range. P3 holds if the T10 pass count is within 2
to 7. P4 is the verdict itself. P6 is scored only if those tasks run.
