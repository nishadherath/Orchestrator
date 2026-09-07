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
5), and a confirmation phase (R_confirm = 9, Wilson lower bound above
0.7, the cell below failing the same bar), which the pilot deliberately
skipped. R_confirm = 9, not the 8 `docs/BENCHMARK-DESIGN.md` originally
specified: 8 could never clear its own reporting bar even at a perfect
8 of 8 (D15, corrected the same day this document was written, before
any run was made against it).

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
pilot and again by D15's R_confirm correction, is about USD 30 to 103 for
the whole benchmark, dominated by a guess for T2, T4, and T6 because the
pilot tested neither a long-horizon task nor a task without an existing
row. The frontier predictions above narrow that guess: if T1, T3, and T5
clear at the floor as predicted (12 runs each, no cell below to also
confirm), that is about USD 5.5 together, close to the design's own
figure for the short-horizon group. If T2 and T4 clear one or two rungs
up rather than the assigned row's higher tiers, and T6 needs several
rungs but not the very top, a tighter total than the design's own USD 30
to 103 is plausible, something closer to USD 22 to 65. Predict the
actual total lands inside the design's wider range regardless of where
in it; falsified by a total under USD 17 (would mean even the predicted
floor-clearing tasks cost less than the pilot's own measurement
suggests) or over USD 103 (would mean the design's upper bound, already
revised twice, still understated the long-horizon tasks).

**Wall clock.** `docs/BENCHMARK-DESIGN.md` already flags this as the real
constraint: three long-horizon tasks serially, each potentially needing 27
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

## Outcome

Run 2026-09-07 11:52, `--confirm --record`, bundle `2026-09-06-04d2acc`, at
harness commit `d3470a7`. Full table in
`test/results/2026-09-07-benchmark-04d2acc.md`. 90 runs total, USD 15.0132,
72.6 minutes of summed wall clock, longest single run 121.5 seconds.

**Frontier cell.** Five of six tasks confirmed at `worker-sonnet-low`, the
cheapest cell on the whole ladder, each at 9 of 9 (Wilson lower bound
70.1%, clearing 0.7):

| Task | Row's assigned cell | Predicted stopping cell | Actual confirmed cell |
| :--- | :--- | :--- | :--- |
| T1 | `worker-sonnet-low` | `worker-sonnet-low` | `worker-sonnet-low`, matched |
| T2 | none | `worker-sonnet-low` or `worker-sonnet-medium` | `worker-sonnet-low`, matched the cheaper option |
| T3 | `worker-sonnet-medium` | `worker-sonnet-low` | `worker-sonnet-low`, matched, one rung below the assigned row |
| T4 | `worker-sonnet-xhigh` | `worker-sonnet-medium` or `worker-sonnet-high` | not confirmed; invalidated (see below) |
| T5 | `worker-opus-high` | `worker-sonnet-low` | `worker-sonnet-low`, matched, three rungs below the assigned row |
| T6 | `worker-fable-xhigh` | `worker-opus-high` or `worker-opus-xhigh` | `worker-sonnet-low`, six rungs below the assigned row and below the prediction too |

T4's search climbed exactly as predicted for the row (`worker-sonnet-xhigh`,
2 of 3, met the steering threshold, matching ROUTING.md's assigned cell for
this triple precisely), but confirmation returned 3 of 9 at
`worker-sonnet-xhigh` and 0 of 9 at `worker-sonnet-high`, "Frontier
confirmed: no". All 25 of T4's failing runs, across every cell tested from
`worker-sonnet-low` through `worker-sonnet-xhigh`, cited the identical
grader message ("KVStore still appears 1 time(s)") while also reporting the
full functional test suite passing. That is a fixture defect, not a
capability result: the pristine `store.py`'s own docstring named the class
it describes, which the grader's strict recursive grep counted alongside
genuine leftover code. Fixed and recorded as D16; T4's row in this table is
not evidence either way and needs a fresh run against the corrected
fixture.

T6 is the sharpest finding here. F13, its fixture backing, was independently
reviewed and confirmed by Jeb before this run, specifically because it
looked closely analogous in shape. It cleared six rungs below that row, the
full width of the ladder, not the two or three rungs the routing table's
other judgement calls have shown so far. Read together with T3 and T5 also
clearing below their assigned rows, five of five valid results this run
landed at the ladder's floor. That pattern is itself worth flagging on its
own terms before touching ROUTING.md: it is at least as consistent with
these particular fixtures being easier than the open-ended work they stand
in for as it is with the table's judgement-set rows being systematically
over-provisioned, and this run cannot distinguish the two. The T4 defect
found this same session is a reminder that a fixture can look right and
still not test what it claims to; five-for-five at the floor is a reason to
look hard at the fixtures themselves before drawing a routing conclusion
from them, not a reason to wait indefinitely.

**Tokens and wall clock.** Tokens remain unscored: `render()` still writes
each run's raw `usage` JSON rather than a computed total, the same gap the
pilot's outcome noted, since the `usage` field's exact shape is itself
unverified (docs/FINDINGS.md). Wall clock held for every group. T1, T3, T5
(predicted under 60 seconds at the floor cell): T3 and T5 stayed under 42
seconds throughout; T1 ranged 30.7 to 67.6 seconds, one run over the
60-second target but nowhere near the 180-second falsification bar. T2, T4
(predicted under 3 minutes): T2 ranged up to 121.5 seconds, T4 up to 119.0
seconds, both comfortably inside the 180-second target. T6 (predicted under
6 minutes at an assumed opus-tier cell): ranged 19.6 to 41.5 seconds,
because it cleared at the floor rather than needing the tier the prediction
assumed, so the number holds without testing what it was meant to test.

**Grader reliability.** T1, T2, T3, T5, T6: zero false results across 60
runs, as predicted for deterministic mechanical and structured graders. T4:
predicted zero false results on the strength of catching one instance of
this defect class during fixture construction; that confidence was wrong.
25 of 30 runs, 83%, were false negatives from a second instance of the
identical defect. Worth stating plainly rather than folding into the
frontier discussion above: a grader that has been checked once for a
failure mode is not thereby cleared of a second occurrence of the same
mode, and this project's own testing discipline caught it again only
because the failure pattern in the real run was this uniform.

T6's report-phrasing prediction (at least one correct diagnosis phrased
without the literal `tax.py` or `get_tax_amount`) is unscored: `report_text`
is only captured on a failing run, by design, and all 12 of T6's runs
passed. Same situation the pilot recorded for T5's grader; no data either
way yet.

**Reset reliability.** Zero `reset_task` failures across all 90 runs, as
predicted.

**Harness-level errors.** Zero forwarder-side failures across all 90 runs,
and zero runs reached the 1200-second `--timeout` ceiling (longest run,
121.5 seconds), both as predicted.

**Containment.** Checked directly in `orchestrator-scratch`: every modified
or new file sits inside a `bench-T*/` directory, `__pycache__/` directories,
or the checkpoint file at the project root (`.benchmark-checkpoint.jsonl`,
this session's own resume feature, working as intended). `RESEARCH_NOTES.md`
and `ai_authorship_detector.py` still show modified, the same two files the
pilot's outcome flagged; their modification times (2026-09-06, ahead of
this run's 2026-09-07 11:52 start) confirm they predate this run and are
unrelated to it, same finding as the pilot. Zero containment violations, as
predicted.

**Cost.** USD 15.0132 total, below this document's own stated falsification
floor of USD 17. That is not a measurement surprise so much as the same
finding as the frontier section from a different angle: the design's cost
estimate assumed T2, T4, and T6 would each need to climb one or more rungs
and, for T4 and T6, that a confirmation phase would run at a pricier tier.
Five of six tasks instead cleared at the cheapest cell on the first attempt,
so the run never spent the money the estimate priced in for climbing. The
prediction is formally falsified on the low side; the reason is the same
over-provisioning pattern already under discussion above, not an error in
the cost arithmetic itself.

**Wall clock.** 72.6 minutes summed across all 90 runs, comfortably inside
the three-hour prediction (falsified only past five hours).

**What this does and does not mean.** T1's row holds cleanly, the one
result fully consistent with its assigned cell. T2 is the first
fixture-backed data point for D13's permanent mechanical-long-horizon gap,
and it clears cheaply, exactly the outcome this document said would argue
for leaving that gap alone. T3 and T5 both clear below their assigned rows,
extending the over-provisioning pattern the pilot first found with T5 alone
to a second and third triple, T5 now at the confirmed reporting bar rather
than search-only steering signal. T6 is the standout: a fixture-backed row,
independently reviewed, cleared six rungs below where it was pinned. T4's
result is not usable and needs a fresh run before it means anything.
Taken together, this is enough to say the routing table's judgement-set
rows warrant a closer look, but the uniformity of the result (five for five
at the floor, on the same day a second fixture defect was found) is reason
enough to check the surviving fixtures (F04, F09, F13 in particular) for
their own version of T4's problem before treating this as settled evidence
against ROUTING.md itself.

## Replication, pending: both fixture fixes in place

Written before the replication run, per the same pre-registration
discipline as the original document. D16 (T4's docstring self-reference)
and D17 (T6's docstring case hint) are both fixed and reverified; this is a
full fresh run of all six tasks, not just the two changed ones, so T1, T2,
T3, and T5 also get an independent replication of an unusually uniform
result (five of five valid tasks landing at `worker-sonnet-low` last time).

**T1, T2, T3, T5.** Unchanged fixtures. Predict each replicates its
confirmed cell exactly: `worker-sonnet-low`, 9 of 9.

**T4.** D16 removed the only source of every prior failure; nothing else
about the port's difficulty changed. Predict the search phase no longer
needs to climb to `worker-sonnet-xhigh` to meet the steering threshold, and
the confirmed cell lands well below the original row, plausibly
`worker-sonnet-low` itself, matching the pattern the other five tasks
already showed. Confirming at `worker-sonnet-xhigh` or above, the original
row, would be the surprise here: it would mean the docstring was never the
sole cause and something else in the port's difficulty was being masked
alongside it.

**T6.** D17 removed a hint, not a grading defect, so the honest prediction
is a smaller shift than T4's, not a guaranteed one. Predict the confirmed
cell moves up from `worker-sonnet-low` by at least one rung now that the
case mismatch is not signposted in the same file as the reproduce path;
anything from `worker-sonnet-medium` up would support the hint as a real
contributor. Confirming again at `worker-sonnet-low` unchanged would argue
the six-rung gap was never mostly about the hint, and F13's row deserves
the closer look on its own terms.

Command: `python3 test/harness/benchmark.py --project <orchestrator-scratch> --confirm --record --fresh`

## Outcome, replication

Run 2026-09-07 14:29, `--confirm --record --fresh`, bundle
`2026-09-06-04d2acc`, at harness commit `a219d55`. Full table in
`test/results/2026-09-07-benchmark-04d2acc.md` (the same filename as the
first run; the first run's content is preserved in git history at commit
`a6b7426`). 72 runs, USD 10.8043, 48.0 minutes summed wall clock, longest
single run 119.2 seconds. Zero failing runs anywhere in the file, zero
harness-level errors, zero containment violations (the same two pre-
existing, unrelated files as both prior runs, `RESEARCH_NOTES.md` and
`ai_authorship_detector.py`, again untouched by this run).

**All six tasks confirmed at `worker-sonnet-low`, 9 of 9, Wilson lower
bound 70.1%.** T1, T2, T3, and T5 replicated exactly, as predicted. T4 and
T6 are the two results this replication was for:

- **T4**: search never needed to test above `worker-sonnet-low`, meeting
  the steering threshold on the first cell (3 of 3). This is a stronger
  result than the prediction asked for ("plausibly `worker-sonnet-low`
  itself"): with D16's docstring defect gone, T4 turned out not merely to
  clear below its assigned `worker-sonnet-xhigh`, but to sit at the exact
  same floor as every other task. The original run's confirmation failure
  was entirely the fixture defect; there is no residual difficulty here
  once the grader stops false-failing correct ports.
- **T6**: unchanged at `worker-sonnet-low`, not the "at least one rung up"
  the D17 prediction expected if the docstring hint were a real
  contributor to the original six-rung gap. It was not: the gap between
  `worker-sonnet-low` and the fixture-backed `worker-fable-xhigh` row
  stands at its full original width, on a fixture now cleared of the one
  hint found in it. Fixing the hint was still the right call (a fixture
  should not signpost its own answer, regardless of what removing the
  signpost does to the result), but it does not explain the gap. F13's row
  itself is the remaining question.

**Wall clock.** T1, T3, T5 stayed under 52 seconds throughout (T1: 28.2 to
51.3s; T3: 28.0 to 44.5s; T5: 20.7 to 39.8s). T2 and T4 stayed under 2
minutes (T2: 32.1 to 119.2s; T4: 40.4 to 54.7s, tighter and more consistent
than the first run's `worker-sonnet-xhigh` cells, as expected at a cheaper
cell). T6: 19.0 to 43.4s.

**What this settles.** Six for six at the ladder's floor, with zero
failures anywhere in a 72-run replication, is no longer explainable by a
fluke in either direction. T1's row holds. T2 is now a well-supported
fixture-backed case for leaving D13's permanent gap alone. T3 and T5
confirm over-provisioned rows a second time each, cleanly. T4 turned out to
have no real difficulty once D16's defect was removed, so it is not a
finding against `worker-sonnet-xhigh` at all, only against the fixture that
used to obscure the true floor. T6 is the one result that survived direct
scrutiny (its one identified hint, removed) and still shows the widest gap
in the set: `worker-fable-xhigh`, a row independently reviewed and
confirmed before this benchmark existed, six rungs above where its own
fixture-backed evidence now sits twice over. That is no longer a reason to
audit the fixture further; it is a reason to look at the row.
