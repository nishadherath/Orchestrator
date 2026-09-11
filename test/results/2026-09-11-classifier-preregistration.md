# Pre-registration: the two-stage classifier measurement

Written 2026-09-11 by Claude (Opus 5, xhigh), `docs/PLAN.md` Stage 5.4,
before any of the runs below. Predictions are fixed here so that the gap
between prediction and measurement is available afterwards, which is the
point of writing them down (`ENGINEERING_PERSONA` 6.2). The design being
tested is `docs/CLASSIFIER-DESIGN.md`, recorded as D39.

Stage 6 runs this. Nothing here changes after the first run.

**Correction, 2026-09-11, before any of B, C or D was run.** This document
originally named configurations C and D's model "sonnet-low", a worker cell
name, without checking whether a bare `--model` argument to `claude -p`
could express effort at all. It cannot: `score_routing.py`'s `--model`
takes only `sonnet`, `opus` or `fable`, and effort needed a separate
mechanism, unconfirmed until now (E23, `docs/FINDINGS.md`: `claude -p
--help` lists a top-level `--effort` flag, distinct from a subagent's
frontmatter effort). `score_routing.py` gained a matching `--effort`
argument in the same commit that found this (Stage 6.2, `docs/PLAN.md`).
Every "sonnet-low" below is corrected to "sonnet, effort low", and the
run commands now show both flags. This is an implementation-detail
correction, made before any measurement it affects had happened; no
prediction, threshold or decision rule below is touched.

## The configurations

| Id | Configuration | Model | Assessment seen by the model | New spend |
| :--- | :--- | :--- | :--- | :--- |
| A | Current prose table, assess and select | opus | Rubric and destination table | None. Already measured at reporting grade |
| B | Two-stage, five fields | opus | Rubric only, no destination table | 3 runs, steering |
| C | Two-stage, five fields | sonnet, effort low | Rubric only, no destination table | 3 runs, steering |
| D | Two-stage, two axes plus the two extra fields | sonnet, effort low | Rubric only, horizon not requested | 3 runs, steering |

A is `test/results/2026-09-11-routing-opus-af94deb-summary.md`: 155 of 162,
95.7 percent, 95 percent Wilson [91.4 percent, 97.9 percent], at USD 0.1645
per verdict. It is not re-run.

B isolates the mechanism, holding the model constant against A. C is the
shipping candidate, because the cost case requires a cheap router. D is the
two-axis variant.

Whichever of B, C or D is the shipping candidate after steering is then run
at nine runs for a reporting-grade result. Nothing is described as confirmed
below that (D37).

## What is measured

For every configuration: agreement per field, agreement on all fields at
once, and cell agreement derived in code from the fields. All three are
reported, and so is the gap between all-field agreement and cell agreement,
because that gap is the forgiveness the current metric hides. Measured at
33.3 percent of single-field errors in `docs/CLASSIFIER-DESIGN.md`.

Cost per verdict is recorded for every configuration, per acceptance
criterion 6.

**D is not scored on cell agreement.** Dropping an axis changes what the
correct answer is, and the fixtures encode three-axis answers; scoring D
against the existing `expected_cell` values would mark it wrong on four of
seventeen by construction (F03, F05, F07, F10, all collapsing to the floor).
D is scored on agreement for the fields it retains, which is directly
comparable with B and C on those same fields.

## Predictions

Written before the runs. Each is a range with a centre.

| Quantity | Prediction |
| :--- | :--- |
| B, cell agreement | 93 to 97 percent, centre 95 |
| B, all-five-field agreement | 78 to 88 percent, centre 83 |
| B, cost per verdict | USD 0.10 to 0.14 |
| C, cell agreement | 75 to 88 percent, centre 82 |
| C, all-five-field agreement | 60 to 75 percent, centre 68 |
| C, cost per verdict | USD 0.01 to 0.03 |
| D, retained-field agreement | 72 to 85 percent, centre 79 |
| D, cost per verdict | USD 0.01 to 0.03 |

The reasoning behind the two that matter most:

**B is predicted to be indistinguishable from A on cell agreement.** The
attractor affects a minority of fixtures, so removing the menu should not
move an aggregate that is already at 95.7 percent. Predicting a null result
here is deliberate: if B comes in materially above A, the attractor is a
larger effect than the historical evidence suggests, and if it comes in
materially below, the table was carrying useful guidance that the rubric
alone does not.

**F09 is the fixture to watch.** It is the current worst at 4 of 9, and it
fails by over-provisioning to `worker-opus-high`, which is the cell for
open, medium, contained. Its confirmed assessment is open, short, contained.
So the failure is a horizon misread, and the suite's sensitivity-to-horizon
confound (open tasks are long in 5 of 7 cases) is a plausible cause. Removing
the table does not remove the confound. Prediction: F09 improves but does not
reach the bar, landing between 5 and 7 of 9.

## The decision rule for shipping

A two-stage configuration ships only if all three hold. The rule is fixed
here and is not revised after the numbers arrive.

1. **Non-inferior on accuracy.** Its cell agreement at reporting grade has a
   95 percent Wilson lower bound not below A's, which is 91.4 percent.
2. **Cheap enough to change the economics.** Its measured cost per verdict is
   below **USD 0.0532**. That ceiling is derived, not chosen: the observed
   floor-failure rate is 0 of 8 benchmark tasks, whose 95 percent Wilson
   upper bound is 32.4 percent, and routing can only pay when the router
   costs less than the floor-failure rate times one floor run, which is
   0.324 times USD 0.1641. A router above that ceiling cannot pay for itself
   at any failure rate the current evidence permits. The opus router measured
   on 2026-09-11 exceeds it by 3.1 times.
3. **Stated honestly against B0.** The decision entry reports cost per
   verdict beside B0's zero, per criterion 6. If the shipped configuration
   still loses to B0 on cost, the entry says so plainly and records that the
   shipping decision rests on the insurance case, P05, which criterion 7
   requires to be stated in `ROUTING.md` itself at close-out.

If no configuration clears rule 2, none ships, and the prose table stands.
That outcome is a result, not a failure: it would say the routing mechanism
cannot be made cheap enough to pay for itself on this evidence, which is
directly useful to Stages 7 and 8.

## What a null result on D means, agreed in advance

`docs/CLASSIFIER-DESIGN.md` establishes that this fixture suite cannot decide
the two-axis question, for two independent reasons: the suite confounds
sensitivity with horizon at a 35 point prediction lift, and dropping an axis
changes the correct answers the fixtures encode.

So it is agreed here, before the run, that **D scoring close to C is
uninformative** and is not evidence that horizon can be dropped. Deciding
that needs fixtures built to break the confound, mechanical work at a long
horizon and open work at a short one, or the cost-per-solved-task measurement
Stage 7 makes possible. D is run because the marginal cost once the flag
exists is a few dollars, not because the result will settle anything.

D additionally rests on P29, that `compact_boundary` reliably signals an
undersized cell, which is unverified and is what E20 measures. E20 should run
before D's result is given any weight.

## Commands

Added 2026-09-11 alongside the "sonnet-low" correction above, since the
original text described the four configurations without ever giving the
concrete invocation Jeb runs. All four are run from
`C:\Users\Bob\Desktop\Code\Claude\Orchestrator`. B, C and D require a
`dist-rubric-only/` install (`python3 tools/build_dist.py --rubric-only`,
Stage 6.1) in a project separate from the one running configuration A's
prose baseline, per the implementation constraints below; `<rubric-project>`
names that project.

```
# B: two-stage, five fields, opus
python3 test/harness/score_routing.py --project <rubric-project> --model opus --classifier two-stage --runs 3 --record

# C: two-stage, five fields, sonnet at effort low (the shipping candidate)
python3 test/harness/score_routing.py --project <rubric-project> --model sonnet --effort low --classifier two-stage --runs 3 --record

# D: two-stage, two axes, sonnet at effort low
python3 test/harness/score_routing.py --project <rubric-project> --model sonnet --effort low --classifier two-stage --axes 2 --runs 3 --record
```

Whichever of B, C or D clears the decision rule's shape at steering grade
runs again at `--runs 9` in place of `--runs 3` for the reporting-grade
result the rule actually requires.

## Implementation constraints that protect validity

**Remove the destination table, not all of section 2.** `ROUTING.md` section
2 carries three things: the instruction to route to the cheapest sufficient
cell, the destination table, and the constraints paragraph. Only the table is
the menu that causes the attractor. The constraints carry real guidance,
including the tie-break wording that defines the `self_directed` field, and
the instruction not to round up. A rubric-only variant that deletes the whole
section changes more than one variable and its result would not be
attributable to the table.

**One consumer project per configuration, or a verified reset between them.**
The rubric-only bundle and the current bundle must not both be installed in
the same project during a run.

**Confirm the two new fixture fields before the run.** TABLE-DATA and the
five-field schema need `self_directed` and `prior_failure` recorded on the
fixtures. For F14 and F18 this is transcription of what their own task text
and rationale already say; for the other fifteen the values are the defaults.
Jeb confirms them as he confirms any fixture label.

## Expected failure shapes

| Shape | Predicted rate | What it would mean |
| :--- | :--- | :--- |
| Unparsed assessment, model emits prose instead of the enumerated line | Under 2 percent for opus, under 8 percent for sonnet at effort low | The schema is not forced hard enough; the fix is prompt shape, not model |
| Model refuses or clarifies when the table is absent | Under 5 percent | The table was carrying more than destinations, and the rubric alone underspecifies the job |
| `self_directed` set true far more often than the one fixture that needs it | Plausible, and the main new risk | An unanchored boolean invites yes; if it fires above 20 percent the field needs a sharper definition or removal |
| Cost per verdict for C above USD 0.0532 | Under 20 percent | The cheap-router route to rung 2 closes, and the dissolution check's conclusion stands unchallenged |

## Cost

| Configuration | Calls | Estimate |
| :--- | :--- | :--- |
| A | 0, already measured | USD 0 |
| B, 3 runs | 54 | About USD 6 to 8 |
| C, 3 runs | 54 | About USD 0.50 to 1.60 |
| D, 3 runs | 54 | About USD 0.50 to 1.60 |
| Reporting-grade run for the shipping candidate, 9 runs | 162 | About USD 2 to 5 at sonnet, effort low, about USD 20 to 26 at opus |

Total: roughly USD 10 to 15 if the shipping candidate is the sonnet,
effort low configuration, roughly USD 30 to 40 if it is the opus one. Both are below the
plan's Stage 6 estimate of USD 45 to 72, because Stage 3.3's baseline removed
the need to re-measure configuration A.

## Outcome

To be completed by Stage 6, after the runs, without editing anything above.
