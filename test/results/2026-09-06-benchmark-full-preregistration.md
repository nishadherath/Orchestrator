# Pre-registration: the full six-task benchmark

Written and committed before the run. The commit adding this file is the
proof of precedence, at HEAD `dfb5e43` (T6, the last fixture this document
depends on).

## What this run is for

Per D14 and `docs/BENCHMARK-DESIGN.md`, this is the measurement the pilot
was staged to size, not a repeat of it. All six tasks (T1 through T6) now
have fixtures, each verified by hand against a pristine state, a correct
reference answer, and at least one plausible wrong answer before being
trusted. This run uses the design's real protocol, not the pilot's
loosened one: R_search = 3 (not 5), steering threshold 2 of 3 (not 4 of
5), and a confirmation phase (R_confirm = 8, Wilson lower bound above
0.7, the cell below failing the same bar), which the pilot deliberately
skipped.

## Design

`python3 test/harness/benchmark.py --project <orchestrator-scratch> --confirm --record`

No `--tasks` flag: the default picks up every task directory under
`test/fixtures/benchmark/`, which is now all six. No `--pilot`: that flag
selects R_search = 5 and the T1/T5 subset only. Forwarder model: sonnet,
the same choice as the pilot and for the same reason (spawning exactly one
named worker is itself mechanical and short, so a fixed cheap forwarder
keeps it from becoming a hidden confound).

## Predictions

**Frontier cell.** The search phase climbs the ladder from `worker-sonnet-low`
for every task regardless of the row ROUTING.md already assigns it
(`benchmark.py`'s `search()` always starts at `LADDER[0]`), which is what let
the pilot discover T5 clearing three rungs below its assigned row. That
result changes what counts as a reasonable prediction here: a routing row
set by judgement, not measurement, is now known to be capable of
over-provisioning, not just under-provisioning, so "predict the assigned
row" is no longer the safe default it would have been before the pilot.

| Task | Row's assigned cell | Fixture backing | Predicted stopping cell | What would be surprising |
| :--- | :--- | :--- | :--- | :--- |
| T1 | `worker-sonnet-low` | F01, F02, F15 | `worker-sonnet-low`, first rung (already measured 5 of 5 in the pilot) | Needing to climb at all |
| T2 | none | none (D12/D13's permanent gap) | `worker-sonnet-low` or `worker-sonnet-medium`: a mechanical rename repeated across thirty files is not made harder by the count, only less forgiving of a missed occurrence | `worker-sonnet-high` or above: would mean sheer volume, not capability, drives this axis, contrary to D13's own reasoning for dropping the row |
| T3 | `worker-sonnet-medium` | F04 | `worker-sonnet-low`, on T1 and T5's pattern: a single function against a fully supplied, already-failing test suite is about as narrowly scoped as work gets | `worker-sonnet-medium` or above: would mean this row, unlike T5's, is not over-provisioned |
| T4 | `worker-sonnet-xhigh` | F07, F08 | `worker-sonnet-medium` or `worker-sonnet-high`: the port's contract is fully specified, so the obstacle is consistent coverage across six files, not judgement | `worker-sonnet-xhigh`: would confirm the row rather than find it over-provisioned |
| T5 | `worker-opus-high` | F09 | `worker-sonnet-low`, first rung (already measured 5 of 5 in the pilot) | Any cell above `worker-sonnet-low` |
| T6 | `worker-fable-xhigh` | F13 (an open, long, contained diagnostic-report task, closely analogous in shape) | `worker-opus-high` or `worker-opus-xhigh`: real judgement is needed to trace a chain of three files, but nothing here demands the sustained, self-directed replanning F13's row is reserved for | `worker-fable-xhigh` (would confirm F13's row rather than find it over-provisioned), or failing to clear the ladder at all |

T2 has no row and no fixture to anchor a prediction against; per
`docs/BENCHMARK-DESIGN.md`, it is "the one triple this benchmark could newly
justify rather than confirm." T6 is the opposite case: it already has a
close fixture analogue (F13), independently reviewed and confirmed by Jeb,
so a result well below `worker-fable-xhigh` would be the first evidence
that even a judgement-based fixture, not only a judgement-based row, can be
over-provisioned.

**Tokens and wall clock.** The pilot measured `worker-sonnet-low` on a
short-horizon, contained task at USD 0.07 to 0.25 per run and 23 to 42
seconds. That figure grounds T1, T3, and T5 if they clear at the floor as
predicted above.

| Task group | Predicted per-run figures at the clearing cell | Falsifies the prediction |
| :--- | :--- | :--- |
| T1, T3, T5 (predicted floor cell) | under 15k tokens, under 60 seconds | 25k tokens or 3 minutes or more |
| T2, T4 (predicted low-to-mid cell) | under 40k tokens, under 3 minutes | 80k tokens or 6 minutes or more |
| T6 (predicted opus-tier cell) | under 80k tokens, under 6 minutes | 150k tokens or 10 minutes or more, the 2026-09-05 dogfood run's own figures for a comparable open, long, `worker-fable-xhigh` task |

**Grader reliability.** T1 and T2 (mechanical, suite plus exact count) and
T3 and T4 (structured, supplied tests, T4 also a grep-based check that the
old interface is gone) are all deterministic and predicted to produce zero
false results, the same prediction the original design made for T1 and the
same reasoning: these graders have no room for a correct answer to read as
a failure. T4's grader was already caught mis-firing once during fixture
construction, on its own test file's docstring naming the retired class in
prose, and fixed before being trusted, which is the reason for confidence
here rather than a residual risk.

T5's report grader already has one clean data point (5 of 5 in the pilot,
against the original prediction of at least one paraphrase-driven false
negative). Predict it continues to hold. T6's report grader is new and
untested against real worker phrasing: predict at least one run across the
benchmark where a correct diagnosis is phrased without the literal strings
`tax.py` or `get_tax_amount` (for example, "the tax lookup function" or
"the region rate table"), the same prediction the original design made for
T5's grader before it was measured. Finding zero such cases would again be
worth noting as evidence the grader survives real phrasing, not a licence
to skip a manual read of any failing T6 reports.

**Reset reliability.** Predict zero `reset_task` assertion failures across
every run, now across six task subtrees instead of two. `reset_task` is
unguarded in `run_one()`, so a failure here would abort the run rather than
let it finish, same as the pilot.

**Harness-level errors.** Unlike the pilot, this pattern is now measured:
zero forwarder-side failures (a refusal, an unparseable reply, a spawned
worker that is not the one asked for) across all 10 pilot runs. Predict
the rate stays low, under 1 in 20 runs across the full benchmark; anything
higher would need investigating on its own, separately from any task's
measured frontier. Also predict zero runs hit the forwarder's own
`--timeout` ceiling (1200 seconds per `claude -p` call): the one
comparable long-horizon data point, the 2026-09-05 dogfood run, finished
in 6 minutes 14 seconds, well inside that budget. A timeout here would be
harness noise, not a capability signal, and would need its own
investigation rather than being folded into a task's pass rate.

**Containment.** Nothing stops a worker from editing outside its assigned
`bench-<task>/` directory beyond the handover telling it to stay there,
the same gap the pilot noted and found no instance of. Predict no such
case across any of the six subtrees, checked the same way as the pilot: a
`git status` across the whole project after the run, not only inside each
`bench-<task>/`.

**Cost.** `docs/BENCHMARK-DESIGN.md`'s own estimate, revised after the
pilot, is about USD 27 to 95 for the whole benchmark, dominated by a
guess for T2, T4, and T6 because the pilot tested neither a long-horizon
task nor a task without an existing row. The frontier predictions above
narrow that guess: if T1, T3, and T5 clear at the floor as predicted (11
runs each, no cell below to also confirm), that is about USD 5 together,
close to the design's own figure for the short-horizon group. If T2 and
T4 clear one or two rungs up rather than the assigned row's higher tiers,
and T6 needs several rungs but not the very top, a tighter total than the
design's own USD 27 to 95 is plausible, something closer to USD 20 to 60.
Predict the actual total lands inside the design's wider range regardless
of where in it; falsified by a total under USD 15 (would mean even the
predicted floor-clearing tasks cost less than the pilot's own measurement
suggests) or over USD 95 (would mean the design's upper bound, already
revised once, still understated the long-horizon tasks).

**Wall clock.** `docs/BENCHMARK-DESIGN.md` already flags this as the real
constraint: three long-horizon tasks serially, each potentially needing 25
runs at several minutes for the pricier cells, could run well over an
hour on their own. Predict the whole run, all six tasks, finishes inside
three hours of wall clock. Falsified by anything past five hours, which
would be worth weighing against splitting the run into two sittings by
cost tier rather than running all six tasks back to back.

## What each outcome means

- T2 clears cheaply (`worker-sonnet-low` or `worker-sonnet-medium`): first
  fixture-backed evidence that mechanical, long-horizon work does not need
  its own row, and D13's permanent gap should stay permanent rather than
  be revisited. Per D13's own reversal condition, the fixture comes first;
  a row, if any, follows it.
- T2 needs `worker-sonnet-high` or above: the opposite finding, and D13's
  gap should be reconsidered with this fixture as the backing it lacked in
  2026-09-06, though what row to add is a separate question from whether
  one is needed.
- T3 or T4 clear below their assigned row: the same over-provisioning
  pattern T5 already showed in the pilot, now appearing on a second and
  third triple, which would argue the routing table's judgement-set rows
  are systematically too expensive rather than T5 being a one-off.
- T5 confirms clearing at `worker-sonnet-low` at the strict reporting bar
  (Wilson lower bound above 0.7, `worker-sonnet-medium` failing the same
  bar): the pilot's result stops being steering signal and becomes a
  reportable finding against ROUTING.md's current `worker-opus-high` row
  for this triple, the first case this benchmark produces of evidence
  against an existing row rather than for a missing one.
- T6 clears below `worker-fable-xhigh`: the first case of a fixture-backed
  row, not merely a judgement-set one, being found over-provisioned by
  measurement, which would say something sharper than any other outcome
  here: even a reviewed and confirmed fixture answer is not a ceiling on
  what the cheapest sufficient cell actually is.
- The T6 grader misses a correct diagnosis: the planted-defect shape needs
  a second matching term or a looser pattern for this fixture specifically,
  the same reversal condition D14 already names for the shape in general.
- Wall clock or cost run well past the predictions: the "run all six in one
  sitting" assumption behind this design needs revisiting before any
  further benchmark task is added to the set.
