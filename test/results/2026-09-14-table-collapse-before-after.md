# Before and after: the eleven-rule table against the four-rule table

Stage 8.5 (`docs/PLAN.md`). Both runs are nine reporting-grade passes of
the eighteen routing fixtures through an opus orchestrator, `score_routing.py`
in assess-and-select mode, no `--effort` flag, same project. The rubric
(`ORCHESTRATOR.md` section 1) is byte-identical between them; only section
2, the table, differs.

- Before: bundle `2026-09-07-af94deb`, eleven rules,
  `2026-09-11-routing-opus-af94deb-summary.md`. 155 of 162 (95.7%, Wilson
  [91.4%, 97.9%]), 16 of 18 fixtures at the bar, USD 15.91.
- After: bundle `2026-09-14-b6605f4`, four rules (D43),
  `2026-09-14-routing-opus-b6605f4-summary.md`. 134 of 162 (82.7%, Wilson
  [76.2%, 87.8%]), 13 of 18 fixtures at the bar, USD 17.71. Claude Code
  2.1.268 against 2.1.263 for the before run.

Nine fixtures changed their `expected_cell` with the table (D43); the
"Expected before" column is what they expected under the old table.
Horizon reads are counted across the nine runs (s short, m medium, l long).

| Fixture | Expected before | Expected after | Agree before | Agree after | Horizon before | Horizon after | Chosen after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F01 | sonnet-low | sonnet-low | 9/9 | 9/9 | s8 | s9 | sonnet-low 9 |
| F02 | sonnet-low | sonnet-low | 9/9 | 9/9 | s9 | s9 | sonnet-low 9 |
| F03 | sonnet-medium | sonnet-low | 9/9 | 9/9 | m8 | m9 | sonnet-low 9 |
| F04 | sonnet-low | sonnet-low | 9/9 | 9/9 | s9 | s9 | sonnet-low 9 |
| F05 | sonnet-medium | sonnet-low | 9/9 | 9/9 | m9 | m9 | sonnet-low 9 |
| F06 | sonnet-high | sonnet-low | 9/9 | 9/9 | m9 | m9 | sonnet-low 9 |
| F07 | sonnet-xhigh | sonnet-low | 7/9 | 9/9 | l9 | l9 | sonnet-low 9 |
| F08 | sonnet-high | sonnet-low | 9/9 | 9/9 | m9 | m9 | sonnet-low 9 |
| F09 | sonnet-low | sonnet-low | 4/9 | 7/9 | m5 s3 | m3 s6 | sonnet-low 7, opus-high 2 |
| F10 | opus-high | opus-high | 9/9 | **1/9** | m9 | **m1 s8** | sonnet-low 8, opus-high 1 |
| F11 | opus-xhigh | sonnet-low | 9/9 | **0/9** | l5 m4 | **m9** | opus-high 9 |
| F12 | opus-xhigh | sonnet-low | 9/9 | **2/9** | l9 | **l2 m7** | opus-high 7, sonnet-low 2 |
| F13 | sonnet-low | sonnet-low | 9/9 | 9/9 | l9 | l9 | sonnet-low 9 |
| F14 | opus-max | opus-max | 9/9 | 9/9 | l9 | l8 m1 | fable-max 6, opus-max 3 |
| F15 | sonnet-low | sonnet-low | 9/9 | 9/9 | s9 | s9 | sonnet-low 9 |
| F16 | clarify | clarify | 9/9 | 9/9 | l9 | l1 m8 | clarify 9 |
| F17 | sonnet-medium | sonnet-low | 9/9 | 9/9 | s9 | s9 | sonnet-low 9 |
| F18 | fable-xhigh | sonnet-low | 9/9 | **7/9** | l9 | l7 m2 | sonnet-low 7, opus-high 2 |

## Reading

Four fixtures regressed at the bar: F10, F11, F12, F18. Two improved: F07
(7 to 9) and F09 (4 to 7). Twelve are unchanged at 9 of 9, including all
six whose expected cell moved to the floor on the sonnet side of the old
table (F03, F05, F06, F07, F08, F17), which the orchestrator now routes to
the floor without hesitation.

Every regression is a horizon read that moved, on an unchanged fixture,
under an unchanged rubric, in the direction that reaches the cell the
orchestrator evidently wanted:

- **F10** is the `open-medium` row's own backing fixture and T10's triple.
  Under the old table opus read it medium nine of nine. Under the new
  table it reads it short eight of nine and sends it to the floor. The
  fixture did not change. What changed is that section 2 now says what the
  `worker-opus-high` row buys (acting against a falsified constraint), F10's
  task (three candidate designs with trade-offs) is visibly not that, and
  the horizon read moved to make the floor the answer.
- **F11** and **F12** are open, consequential root-cause investigations
  whose old expected cell was `worker-opus-xhigh`. Under the old table opus
  read F11's horizon long five, medium four, and F12's long nine, and the
  `open-any-consequential` row made the horizon irrelevant. Under the new
  table, medium is the only path to an opus cell, and the reads are medium
  nine of nine and seven of nine. F18, the same shape with `self_directed`,
  moved two of nine the same way.

This is D13's attractor observed a second time, in the other direction:
D13 saw a row added change the classification of tasks that never routed
to it; this sees rows removed change the classification of the one task
that still does and of two that no longer do. The mechanism is the same.
The horizon read is not made independently of the destination. That was
already the least reliable axis (F03, F05, F08, F11, F18 all corrected on
horizon; `CLAUDE.md` open questions), and D42 recorded that horizon is not
what actually separates T10 from T9 anyway.

The consequence for the four-rule table is direct: its one row above the
floor is not reachable by the orchestrator on the fixture that backs it,
one time in nine, and is reached instead by two fixtures the benchmark
says belong on the floor. A row the orchestrator cannot find on its own
fixture is not a measured routing row, whatever the benchmark measured
about the cell. Per 8.5's rule the change is reopened; see D44.
