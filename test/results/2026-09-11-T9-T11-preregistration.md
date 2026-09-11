# Pre-registration: T9, T10 and T11, a task the floor cannot clear

Written before any run, on the T7 template. The commit adding this file is
the proof of precedence.

## What this run is for

Criterion 1 of `docs/PLAN.md`. Eight benchmark tasks exist and all eight
cleared at `worker-sonnet-low` once each fixture's grader was correct. Every
routing row above the floor is therefore a hypothesis, not a measurement,
and the framework track has no subject until a task exists that the floor
measurably fails. T9, T10 and T11 are built to be that task, in two premise
shapes and one scale shape so the result does not rest on one design.

This run can fail to produce a floor-breaker. That outcome is informative and
is provided for: task 7.3's hardening rule fires once, and if the hardened
tasks clear too, "the floor keeps winning" is recorded as a finding and the
table's rows above the floor stand or fall on that.

## The three tasks

**T9, a false measurement.** `PROBLEM.md` states as established fact that a
past profiling run identified `EventStore.query()` as the bottleneck, and
freezes `store.py` on that basis. The claim is false: `query()` is one dict
lookup and a slice, called once per report. The real cost is the
`line not in out` scan in `_format_rows`, which is quadratic in output size.
The budget is only reachable by disbelieving the stated profiling result.
Measured: 4.57 seconds unfixed at 100,000 events, 0.113 seconds fixed,
against a 1.0 second budget.

**T10, a false constraint.** `PROBLEM.md` freezes `legacy_ids.py` and
justifies the freeze by stating that three downstream systems depend on
`normalise()`'s exact output. The justification is false and checkable in the
repository: all three call sites in `downstream.py` call `.strip()` on the
result themselves, so stripping inside `normalise()` is a no-op for every one
of them. A supplied test pins `normalise()`'s required behaviour directly, so
the frozen file is the only place the fix can go, and a worker that accepts
the constraint without checking its justification cannot pass.

**T11, T7's lineage at a larger scale.** Seven services rather than four, one
root cause shared across three of them, three decoys that look worse on
inspection than the defect does. `shared/registry.py`'s `resolve()` rebuilds
the whole key index on every call, and catalogue, checkout and search each
call it once per record, so all three are quadratic in tenant size.
`resolve()` reads as ordinary code on its own. checkout's per-line
`stretch()` is the largest absolute cost at every size measured but is linear
and is unused by the other two affected services; `serialize.py`'s
`_encode_string` scans a list, which is exactly T7's defect, but the list is
capped so the scan is constant; inventory is last month's largest diff by a
wide margin and is correct. Measured at n of 200, 400, 800 and 1600:
catalogue 0.009, 0.027, 0.135, 0.410 seconds and search 0.013, 0.026, 0.158,
0.652 seconds, quadrupling per doubling, against gateway and inventory
doubling and auth flat. The diagnosis is reachable by running `bench.py` at
more than one size and reading the curve, and is not reachable by reading the
diff or by timing one size.

## Design

```
python3 test/harness/benchmark.py --project <orchestrator-scratch> --tasks T9,T10,T11 --confirm --record --fresh
```

`--fresh` is required, as for T7: the existing checkpoint's `tasks` identity
field does not match this task set. Protocol otherwise unchanged: R_search =
3, steer threshold 2 of 3, R_confirm = 9, 95 per cent Wilson lower bound above
0.7. Ladder: `worker-sonnet-low`, `worker-sonnet-medium`,
`worker-sonnet-high`, `worker-sonnet-xhigh`, `worker-opus-high`,
`worker-opus-xhigh`, `worker-fable-xhigh`.

## Predictions

**The prediction this stage exists to test, stated outright.**
`worker-sonnet-low` fails at least one of T9, T10 and T11 at the reporting
bar. Falsified by all three confirming at the floor.

**Per task.** T9 and T10 are the stronger candidates, because both require
contradicting an instruction the task itself presents as settled, which is a
disposition rather than a capability and is the thing a low effort level is
most likely to skip. Predict T9 and T10 both land above the floor, at
`worker-sonnet-medium` or `worker-sonnet-high`. T11 is the weaker candidate
and is deliberately a control: its lineage cleared at the floor twice (T6,
T7), so if T11 also clears, that is a third data point for the same triple
rather than a surprise. Predict T11 at `worker-sonnet-low` or
`worker-sonnet-medium`.

The prediction is therefore directional, not just a bare disjunction: if the
floor breaks anywhere it breaks on premise rejection, not on scale. If the
opposite happens, that T11 breaks the floor and T9 and T10 do not, the
reading is that scale rather than disposition is what the rows above the
floor are for, which would point Stage 8 in a different direction.

**Grader reliability.** Predict zero false results. All three graders were
tested six ways before this file was written, one more than the five the plan
prescribes:

| Case | T9 | T10 | T11 |
| --- | --- | --- | --- |
| Correct, phrasing 1 | PASS | PASS | PASS |
| Correct, phrasing 2 | PASS | PASS | PASS |
| Plausible wrong 1 | FAIL | FAIL (deferential fix in the caller) | FAIL (blames hashing ROUNDS) |
| Plausible wrong 2 | FAIL | FAIL (correct fix, no artefact) | FAIL (blames the serialize cache, T7's answer) |
| Adversarial | FAIL | FAIL (deferential fix plus deleting the failing test) | FAIL (shotgun list naming every candidate) |
| Sixth case | FAIL | FAIL (no code change, report blames the constraint) | FAIL (blames the inventory rewrite) |

T9's and T10's graders are behavioural rather than string-matching, a
departure from task 7.1's sketch recorded in `docs/PLAN.md` under 7.1. Every
behavioural check runs against a probe the grader writes rather than against
the task's own test files, so editing or deleting those files cannot affect
the verdict. This removes the false-negative-on-phrasing risk that three of
the four earlier graders carried (D16, D17, D30), and the residual risk moves
the other way: a worker that produces the right behaviour for the wrong
reason passes. The report string signals are still computed and printed as
diagnostics, so that case is visible in the result file even though it does
not gate.

T11's grader is a string match, because T11 is diagnose-only, and it carries
the same residual risk every T5 to T8 grader carries: a correct diagnosis
phrased outside the accepted alternations would false-negative. Its third
gating check, that the report state the mechanism, is new and is the most
likely source of a false negative in this run. Flagging it here so that a T11
failure is read against the report text before it is read as a capability
result.

**Tokens and wall clock.** T7, the closest comparable, ran 67.3 seconds mean
in search and 127.8 seconds at its longest. T11 is larger than T7 and predicts
above it. T9 and T10 require editing code and running tests, which T7 did not,
but are single-repository tasks at a much smaller scale, so predict them
between T6's range (19 to 44 seconds) and T7's. Falsified for T11 by anything
at or below T7's mean.

**Containment and reset.** Zero containment violations outside
`bench-T9/`, `bench-T10/` and `bench-T11/`, zero `reset_task` failures. Same
as every prior run.

## Cost

Search is at most 3 runs per cell per task, and stops at the first cell that
clears 2 of 3. Confirmation is 9 runs at the candidate cell plus 9 at the cell
below it, except at the floor where it is 9.

At the predicted frontiers, T9 and T10 climb two or three rungs (6 to 9 search
runs each) and confirm at two cells (18 runs each), and T11 climbs one or two
(3 to 6 search runs) and confirms at one or two cells (9 to 18 runs). That is
roughly 75 to 90 runs. T7's 12 runs cost USD 3.3667, about USD 0.28 per run at
sonnet cells, which puts the predicted case near USD 25.

The upper bound is the case where a task climbs into the opus cells, whose
per-run cost is unmeasured: the only data point above the sonnet cells in this
benchmark is a single fable-xhigh run at 103k tokens. A task that climbs the
whole ladder is 21 search runs plus 18 confirmation runs, and three of those
is 117 runs with the expensive cells weighted heavily.

Estimate **USD 30 to 150**, unchanged from the figure Stage 7 was approved
with. The upper half of that range is uncertainty about the opus cells, not
expectation.

## Outcome

Not yet run.
