# Pre-registration: does asking for a cell distort the assessment?

Written and committed before the run. The commit adding this file is the proof
of precedence.

## The question, and what this can and cannot answer

D13 established that a routing row changes how tasks are classified. That
finding has two possible mechanisms and this experiment separates only one of
them.

- **Output coupling.** The orchestrator is asked for an assessment and a worker
  in one reply. It may settle on a plausible cell and then produce axis values
  that justify it, in which case the assessment is partly a rationalisation.
- **Menu visibility.** Merely having the table in context changes how the task
  is read, whatever the reply is asked to contain.

This experiment tests output coupling only. The table stays in context in both
conditions, because it is part of `ORCHESTRATOR.md`, which the consumer project
appends to its `CLAUDE.md`. A later experiment on a bundle whose
`ORCHESTRATOR.md` carries no table would be needed to test menu visibility, and
nothing here should be read as settling that.

## Design

One variable: whether the prompt asks for a worker. Same fixtures, same model
(sonnet), same bundle (`2026-09-06-04d2acc`), same project, three runs each.

- Control, already measured: `--runs 3`, prompt asks for assessment, worker and
  action. `test/results/2026-09-06-routing-sonnet-04d2acc-*`.
- Treatment: `--runs 3 --assess-only`, prompt asks for the assessment triple
  alone and forbids naming a worker.

Scored on assessment accuracy against the sixteen fixtures that carry a
confirmed assessment. F16 has none and is excluded from both.

## Control, computed from the recorded runs

| Measure | Control |
| :--- | :--- |
| Exact triple, all three axes correct | 27/47 = 57.4% |
| Axis calls correct | 116/141 = 82.3% |
| Sensitivity | 43/47 = 91.5% |
| Horizon | 35/47 = 74.5% |
| Blast | 38/47 = 80.9% |
| Cost per run | USD 0.6302 mean |

## Predictions

If output coupling is real, removing the cell request should improve the
assessment, and most on the horizon axis, which is both the weakest in the
control and the axis F03 bent to reach the row that was removed.

| Measure | Predicted | No-effect band | Falsifies output coupling |
| :--- | :--- | :--- | :--- |
| Exact triple | 60% to 70% | 52% to 62% | 62% or below |
| Axis calls | 84% to 90% | 79% to 85% | 85% or below |
| Horizon axis | 80% to 88% | 70% to 79% | 79% or below |
| Cost per run | USD 0.45 to 0.60 | | above the control |

Within-experiment control: F08's horizon has been read as medium in 11 of 11
observations across three bundles and both models, though its confirmed horizon
is long. It should stay wrong here too. If F08's horizon corrects under
assessment-only, that is a larger effect than predicted and worth investigating
before drawing any other conclusion.

Note on F07: its cell was correct in 3 of 3 control runs while its triple was
never exactly right, because it read the blast as consequential and the
structured long-horizon row ignores blast. Cell agreement can therefore hide an
axis error, which is one reason this experiment scores axes rather than cells.

## What each outcome means

- Predictions hold: the assessment is partly a rationalisation of a chosen cell,
  and separating the two steps is worth designing for. The next question is menu
  visibility, on a bundle without the table.
- No effect: the coupling is not in the output format. Either the menu itself
  changes the reading, which the follow-up would test, or D13's mechanism works
  some third way not yet described.
- Assessment gets worse: the cell request is doing useful work, perhaps by
  forcing the model to commit to something concrete. That would be evidence
  against splitting assessment from routing, and against the schema-forced
  classifier idea.

## Protocol

From the Orchestrator repository, with the current bundle installed in the
consumer project:

```
python3 test/harness/score_routing.py --project <orchestrator-scratch> --model sonnet --runs 3 --assess-only --record
```

Predicted spend about USD 1.50. Output is written with an `-assessonly` tag in
the filename, so it cannot overwrite the control.

## Outcome, added 2026-09-06 after the run

Null. Removing the cell request did not improve the assessment, and the axis
totals are all but identical.

| Measure | Control | Treatment | Predicted | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| Exact triple | 27/47 = 57.4% | 25/48 = 52.1% | 60 to 70% | Falsified, inside the no-effect band |
| Axis calls | 116/141 = 82.3% | 116/144 = 80.6% | 84 to 90% | Falsified, inside the no-effect band |
| Horizon axis | 74.5% | 75.0% | 80 to 88% | Falsified, unchanged |
| Cost per run | USD 0.6302 | USD 0.3602 | 0.45 to 0.60 | Cheaper than predicted |

The within-experiment control held: F08's horizon stayed wrong 3 of 3, now 14
of 14 observations across four run sets.

Output coupling is therefore not the mechanism behind D13. The orchestrator was
not choosing a cell and back-filling axes to justify it; asked for the axes
alone, on the same bundle, it produces the same quality of assessment. By
elimination, D13's effect comes from menu visibility, the table being present in
context at all, which this experiment deliberately could not test because
`ORCHESTRATOR.md` carries the table in both conditions.

Two fixtures moved down, F01 and F15, both 3 of 3 to 1 of 3, and both are the
simplest mechanical, short, contained cases. Two moved up, F10 and F12. With
three runs each these are not distinguishable from noise and no conclusion is
drawn from them.

A defect in the first version of this mode is recorded here rather than
quietly fixed: F16 has no confirmed assessment, and the scorer counted it as
three failures instead of excluding it, which is why the run's own summary file
reads 25/51 (49.0%) rather than the 25/48 (52.1%) used above. The recorded
summary is left as the machine produced it. `score_routing.py` now drops
unscorable fixtures in this mode before spending anything on them.

## What follows

The practical protection against D13 is already in place and does not depend on
knowing the mechanism: ROW-BACKED refuses a row with no fixture behind it, and
CLAUDE.md requires a before-and-after fixture run for any table change. Testing
menu visibility would need a bundle whose `ORCHESTRATOR.md` omits the table, and
it is only worth running if the answer would change what gets built. If the
system is not going to separate assessment from the table, the knowledge is
inert.
