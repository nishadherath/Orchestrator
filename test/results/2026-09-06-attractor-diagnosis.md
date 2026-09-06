# Diagnosis: the "Mechanical, long horizon" row pulls assessments toward itself

Written after the 2026-09-06 sonnet and opus runs, before any patch, per
CLAUDE.md's "diagnostic before patch". No fix is applied here. The proposed
discriminating experiment and its prediction are at the end.

## Observed

D9 added the row `| Mechanical, long horizon | worker-sonnet-high |` to fill a
coverage gap. Two fixtures that were answered correctly before it existed are
answered incorrectly after, and both arrive at the new row from a different
direction.

F03, "move about forty `*.spec.ts` files and fix the imports". Confirmed
assessment mechanical, medium, contained, so `worker-sonnet-medium`.

| Bundle | Model | Assessment | Cell |
| :--- | :--- | :--- | :--- |
| 1708054, no row | sonnet | mechanical, **medium**, contained | `worker-sonnet-medium`, correct |
| 1708054, no row | opus | mechanical, **medium**, contained | `worker-sonnet-medium`, correct |
| 4cf35f7, row present | sonnet, 3 of 3 runs | mechanical, **long**, contained | `worker-sonnet-high`, over-provisioned |
| 4cf35f7, row present | opus, runs 1 and 2 | mechanical, **medium**, contained | `worker-sonnet-medium`, correct |
| 4cf35f7, row present | opus, run 3 | mechanical, **long**, contained | `worker-sonnet-high`, over-provisioned |

F07, "convert thirty callback modules to async/await, one at a time, keeping
the suite green". Confirmed assessment structured, long, contained, so
`worker-sonnet-xhigh`.

| Bundle | Model | Assessment | Cell |
| :--- | :--- | :--- | :--- |
| 1708054, no row | sonnet | **structured**, long, consequential | `worker-sonnet-xhigh`, correct |
| 1708054, no row | opus | **structured**, long, consequential | clarify, cell not chosen |
| 4cf35f7, row present | sonnet, 3 of 3 runs | **mechanical**, long, consequential | `worker-sonnet-high`, under-provisioned |
| 4cf35f7, row present | opus, run 1 | **structured**, long, consequential | `worker-sonnet-xhigh`, correct |
| 4cf35f7, row present | opus, runs 2 and 3 | **mechanical**, long, contained | `worker-sonnet-high`, under-provisioned |

F03 bent its **horizon** to reach the new row. F07 bent its **sensitivity** to
reach it. Neither bent the other axis. They converge on one cell from opposite
errors.

## The control

F08 is assessed structured, medium, consequential in 8 of 8 observations,
across both bundles and both models, and is wrong in the same way every time
(its confirmed horizon is long). Assessment is otherwise stable across the
bundle change. The instability is specific to the two fixtures whose tasks the
new row's label can describe.

## Statistics

Taking the axis that flipped in each fixture (F03's horizon, F07's
sensitivity): correct in 4 of 4 observations before the row existed, and in 3
of 12 after. Fisher exact, one-sided, p = 0.0192. The baseline is only four
observations, so this is suggestive rather than settled, which is what the
experiment below is for.

## Two hypotheses

**H1, the attractor.** A row's presence creates a reachable classification, and
assessments near it are pulled in. The rubric's own instruction to take the
cheapest cell that clears the bar supplies a gradient, but the pull is not
purely toward cheapness: F03 moved up a cell and F07 moved down one. Under H1
the table is not a lookup applied after independent assessment. The menu of
destinations feeds back into how the task is classified.

**H2, revealed ambiguity.** The labels were always ambiguous for bulk
repetitive work. Before the row, "mechanical, long" had nowhere to go, so the
assessor was pushed to a different label by elimination and happened to land
correctly. The row did not create an error; it exposed that the distinction was
never really being made.

The evidence leans to H1. Under H2 the correct answers before the change were
luck, but both models were right on both fixtures at baseline, and the control
fixture shows assessment is otherwise stable across the same change. H2 is not
eliminated: baseline is one run per model, so baseline stability was never
measured.

## Why the obvious fixes do not work

Changing the row's target cell does not address the mechanism, and no single
cell is right for both fixtures: F03's correct cell is `worker-sonnet-medium`
and F07's is `worker-sonnet-xhigh`. Setting the row to either one fixes that
fixture and worsens the other. Tightening the axis definitions might help, but
that is a change to section 1 that would affect every fixture, and it should
not be attempted before H1 and H2 are separated.

## Proposed experiment: revert the row only

One variable. Remove `| Mechanical, long horizon | worker-sonnet-high |` from
`ROUTING.md`, change nothing else, rebuild, and run sonnet three times. Sonnet
rather than opus because sonnet showed the effect in 6 of 6 opportunities, so
it has the most room to move, and because three sonnet runs cost about USD 1.45
against opus's 10.10.

Predictions, recorded before the run:

- F03 returns to mechanical, medium, contained and `worker-sonnet-medium` in at
  least 2 of 3 runs. Currently 0 of 3.
- F07 returns to a structured sensitivity and `worker-sonnet-xhigh` in at least
  2 of 3 runs. Currently 0 of 3.
- F08 stays wrong in the same way, 3 of 3, since nothing touching it changes.
- Overall sonnet agreement rises from 32/51 to about 38/51.

If F03 and F07 recover, H1 holds and the finding is that adding a row can cost
more accuracy than the gap it fills. If they stay wrong, H2 holds, the fix
belongs in the axis definitions rather than the table, and the row can stay.

This experiment requires ROUTE-TOTAL to tolerate a deliberate, documented gap.
That check should gain an allow-list keyed by triple and requiring a stated
reason in `ROUTING.md`, the same shape as its existing tie-break allow-list, so
a gap must be argued for rather than merely left.

## What this implies beyond one row

If H1 holds, every edit to the routing table can change how tasks are assessed,
not only where an assessment routes. That is a feedback loop between the menu
and the classifier, it is invisible to any static check, and the only way to see
it is a before-and-after fixture run. It is also direct evidence for the open
architectural question of whether assessment should be a schema-forced
classifier that never sees the cell list, with the table applied afterwards in
code.
