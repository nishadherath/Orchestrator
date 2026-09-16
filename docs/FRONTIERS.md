# What the benchmark has measured for each routing row

**Superseded 2026-09-16 (docs/PLAN-6.md Stage C.3, B4).** This is a
2026-09-14 snapshot of the eleven-rule table D44 and D45 collapsed the
same day it was written; the rows it describes below no longer exist in
`src/routing_table.json`, which now has one non-escalation rule (the
floor) and one escalation-only rule (the frontier). It stays here
because it is the cited provenance every bucket in
`src/routing_priors.json` traces back to (D64), not because it describes
the current table. `src/routing_priors.json` is the successor document
for what the shipped table currently does; read this file for the
history the priors were built on.

Written 2026-09-14 for `docs/PLAN.md` Stage 8.1. One entry per rule in
`src/routing_table.json`, stating what the benchmark (`test/results/`,
tasks T1 through T11) has measured for the task class the rule covers.
This is the evidence Stage 8.2's design rests on and Gate C decides on.
It is a snapshot; the results files are the record.

## How to read it

A **measured frontier** is a cell that confirmed at the reporting bar
(nine runs, 95 per cent Wilson lower bound above 0.7) on a benchmark task
whose shape matches the rule's triple, with the cell below failing the
same bar. Only `worker-sonnet-low` and `worker-opus-high` have ever
confirmed; every task but one landed at the floor.

A rule is **bracketed** when no task matches its exact triple but tasks at
both ends of the axis it varies on confirmed at the floor. D19 chose not to
extend floor evidence past the exact triple measured. Criterion 3, fixed at
Gate A after D19, says a row above the floor backed by judgement fixtures
alone does not stand, and Stage 8.2's rule is that such a row is removed or
merged downward. Bracketing is recorded here because it is the reason the
merge is not reckless, not because it is a measurement of the triple.

A **policy** rule is one whose only difference from a cheaper rule is blast
radius. `docs/BENCHMARK-DESIGN.md` states that blast radius is unmeasurable
by exit code, because it describes what a wrong answer costs the owner, not
what the worker can do. Such rules rest on risk appetite by construction,
and criterion 3 requires them to say so in `src/ROUTING.md` itself.

An **escalation** rule matches on `prior_failure`, not on an assessed
triple. It is a mechanism, not a capability claim about the task.

Per-task evidence, for reference: T1 mechanical short, T2 mechanical long,
T3 structured short, T4 structured long, T5 open short, T6 and T7 open
long contained, T8 open at F09's review scale, T9 open with a false
measurement, T10 open with a false constraint, T11 open long contained at
T7's scale times two. All confirmed `worker-sonnet-low` at the bar
(T1 to T6 twice each, `2026-09-07-benchmark-04d2acc-{original,replication}.md`;
T4's original attempt was a grader defect, D16 and D17; T7 after D20; T8
after D30; T9 after D41) except T10, which confirmed `worker-opus-high`
9 of 9 with `worker-sonnet-xhigh` 0 of 9 below it
(`2026-09-11-benchmark-af94deb-tasks-T10+T11+T9.md`, D42).

## The rules

### `short-contained` (`worker-sonnet-low`), the floor

Any sensitivity, short, contained. Fixtures F01, F02, F04, F09, F15.
Measured: T1, T3, T5 at their exact triples, T8 at F09's scale. Frontier
`worker-sonnet-low`. Stands.

### `open-long-contained` (`worker-sonnet-low`)

Fixture F13. Measured: T6 (twice), T7, T11, all at the floor. Frontier
`worker-sonnet-low`. Stands. This row was lowered from `worker-fable-xhigh`
by D21 on T6 and T7; T11 is the third confirmation.

### `mechanical-medium` (`worker-sonnet-medium`)

Fixture F03. No task at the exact triple. Bracketed: T1 (mechanical short)
and T2 (mechanical long) both at the floor, twice each. No measured
frontier above the floor. Under 8.2's rule: merge downward to the floor;
F03's `expected_cell` follows.

### `structured-medium-contained` (`worker-sonnet-medium`)

Fixture F05. No task at the exact triple. Bracketed: T3 (structured short)
and T4 (structured long) both at the floor, twice each. No measured
frontier. Under 8.2's rule: merge downward; F05 follows.

### `structured-long` (`worker-sonnet-xhigh`)

Fixture F07. Measured at the exact triple: T4 (structured long, a module
ported to a new interface with the suite green throughout), floor, twice.
No frontier above the floor; this is a direct measurement, not a bracket.
Under 8.2's rule: merge downward; F07 follows. The row's own text does not
distinguish contained from consequential, so the consequential half is a
policy question (below), not a capability one.

### `open-medium-contained` (`worker-opus-high`)

Fixture F10. Measured at the triple, classified after the fact: T10 (open,
because an instruction has to be reclassified; medium, because the work is
read a problem statement, check three call sites, edit, run two suites,
write an artefact, in one repository; contained, because the change is one
function pinned by tests) confirmed `worker-opus-high` 9 of 9 with
`worker-sonnet-xhigh` 0 of 9 below it. T9, the same triple with a false
measurement in place of a false constraint, confirmed the floor 9 of 9.
T8, which opus reads as medium (D26, D28) though F09 assigns short,
confirmed the floor.

**This is the only measured frontier above the floor.** The row keeps its
cell. What it buys is recorded in D42 and is not what the row's text
implies: every failing sonnet run found what opus found and declined to
act against an explicit instruction whose stated reason it had itself
shown to be false. The row is a disposition frontier, not an
intelligence-sensitivity one, and the classification of T10 as this
triple was made after the result was known. Both facts belong in the
row's description in `src/ROUTING.md`.

### `mechanical-short-consequential` (`worker-sonnet-medium`)

Fixture F17. Differs from `short-contained` on blast only. Unmeasurable by
this benchmark. Policy row.

### `structured-short-or-medium-consequential` (`worker-sonnet-high`)

Fixtures F06, F08. Differs from `short-contained` and
`structured-medium-contained` on blast only. Policy row.

### `open-any-consequential` (`worker-opus-xhigh`)

Fixtures F11, F12. Differs from `open-long-contained`, `short-contained`
and `open-medium-contained` on blast only. Policy row. Note that its cell,
`worker-opus-xhigh`, sits above the only measured frontier
(`worker-opus-high`), so even if blast were measurable the row would be
claiming a cell no task has ever reached; T10's ladder stopped at
`worker-opus-high` because the bar was cleared there.

### `open-long-consequential-self-directed` (`worker-fable-xhigh`)

Fixture F18. Differs from `open-any-consequential` on `self_directed`,
which no benchmark task exercises, and from `open-long-contained` on
blast. Policy row on two unmeasured inputs. `worker-fable-xhigh` has one
data point in the whole benchmark, a single 103k-token run, and no task
has reached it on the ladder.

### `frontier` (`worker-opus-max`, escalation only)

Fixture F14. Matches on `prior_failure: failed_at_xhigh`. No benchmark task
has failed at an xhigh cell and been escalated; T10's ladder never reached
one. Escalation mechanism, not a measurement. Stands as mechanism, labelled
as such.

## Summary

| Rule | Cell | Class | Evidence | 8.2 disposition |
| --- | --- | --- | --- | --- |
| `short-contained` | sonnet-low | measured | T1, T3, T5, T8 | stands |
| `open-long-contained` | sonnet-low | measured | T6, T7, T11 | stands |
| `open-medium-contained` | opus-high | measured | T10 (T9 at floor) | stands, description rewritten |
| `mechanical-medium` | sonnet-medium | bracketed | T1, T2 at floor | merge to floor |
| `structured-medium-contained` | sonnet-medium | bracketed | T3, T4 at floor | merge to floor |
| `structured-long` | sonnet-xhigh | measured at floor | T4 | merge to floor |
| `mechanical-short-consequential` | sonnet-medium | policy | none possible | Gate C |
| `structured-short-or-medium-consequential` | sonnet-high | policy | none possible | Gate C |
| `open-any-consequential` | opus-xhigh | policy | none possible | Gate C |
| `open-long-consequential-self-directed` | fable-xhigh | policy | none possible | Gate C |
| `frontier` | opus-max | escalation | not applicable | stands as mechanism |

Three rules merge to the floor on evidence. One rule above the floor is
measured and stays. Four are policy and go to Gate C as risk-appetite
decisions. One is mechanism. If Gate C drops all four policy rows, the
table is the floor, the clarify rule, one measured row and the escalation
rule, which is the dissolution outcome Stage 4.2 described, reached by
measurement rather than by argument.
