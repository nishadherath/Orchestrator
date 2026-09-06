# Pre-registration: the T1/T5 benchmark pilot

Written and committed before the run. The commit adding this file, alongside
`test/harness/benchmark.py` and the T1/T5 fixtures it measures, is the proof
of precedence.

## What this pilot is for

Per D14 and `docs/BENCHMARK-DESIGN.md`, the pilot is not meant to answer the
cost and quality question. It exists to measure the parameters the design
guesses at, so the six-task benchmark can be sized from real numbers instead
of estimates. Nothing below should be read as a claim about the routing
table beyond the two predictions in "Frontier cell" that are worth recording
because they are free: the pilot has to climb the ladder anyway, so noting
where it stops costs nothing extra.

A reading worth stating up front: `docs/BENCHMARK-DESIGN.md` says "full
ladder" for the pilot. `benchmark.py` reads this as the search climbing as
high as it needs to, stopping at the first cell that clears the permissive
steering threshold, not as every rung running unconditionally regardless of
outcome. The design's own cost estimate ("roughly 30 to 50 runs" for two
tasks at R=5) only works out under the stopping reading: exhausting the full
seven-rung ladder unconditionally would be 70 runs before any repeats, and
the 30-to-50 figure implies each task is expected to climb a few rungs, not
run all seven. This is a judgement call about the spec's wording, not a
finding, and is flagged here so it can be corrected if it is wrong.

## Design

`python3 test/harness/benchmark.py --project <orchestrator-scratch> --pilot --record`

Tasks: T1 (mechanical, short: rename `compute_total` to `compute_sum` across
one definition and three call sites) and T5 (open, short: diagnose a planted
discount-calculation bug from a support ticket, report the file and
function). R_search = 5, steering threshold 4 of 5, no confirmation phase.
Forwarder model: sonnet (the trivial "spawn exactly this worker" step is
itself mechanical and short, so it does not need a capable model, and a
fixed cheap forwarder keeps it from becoming a hidden confound in the
results).

## Predictions

**Frontier cell.** ROUTING.md already assigns a cell to each task's
(sensitivity, horizon, blast) triple: `worker-sonnet-low` for mechanical,
short, contained (T1), `worker-opus-high` for open, short or medium,
contained (T5). The pilot cannot confirm a frontier (no confirmation phase),
but the search's stopping point is a first, cheap check on whether those
rows are justified.

| Task | Predicted stopping cell | What would be surprising |
| :--- | :--- | :--- |
| T1 | `worker-sonnet-low`, threshold cleared on the first rung | Needing to climb at all: the table's cheapest row failing its own trivial case |
| T5 | `worker-sonnet-medium` or `worker-sonnet-high`, below the table's `worker-opus-high` | Needing to climb all the way to `worker-opus-high`: it would mean this task, small and narrowly scoped as it is, still needs the table's current, more expensive row |

**Tokens and wall clock.** The one recorded real-work data point is the
2026-09-05 dogfood run, `worker-fable-xhigh` on an open-ended, long-horizon
build task: 102.9k tokens, 6 minutes 14 seconds, 53 tool calls. T1 and T5 are
far smaller and short-horizon by design.

| Measure | Predicted | Falsifies the "these tasks are tiny" assumption |
| :--- | :--- | :--- |
| T1, cell that clears search | under 10k tokens, under 60 seconds | 25k tokens or 3 minutes or more |
| T5, cell that clears search | under 15k tokens, under 90 seconds | 35k tokens or 4 minutes or more |

**Grader reliability.** T1's grader is a deterministic suite run plus a grep
count; predict zero false results across every run, of either sign. T5's
grader is a string match against a relayed report; predict at least one run
across the pilot where a worker's diagnosis is right but phrased without the
literal strings `pricing.py` or `apply_discount` (for example, "the discount
calculation" or "the pricing module"), which the grader would then score as
a fail. Finding zero such cases would be worth noting as evidence the
grader survives real phrasing better than expected, not evidence to skip the
manual check below.

**Reset reliability.** Predict zero `reset_task` assertion failures across
every run. `git checkout` and `git clean -fdx` on a small, known subtree are
mechanical; a failure here would be a defect in the harness, not a finding
about the tasks.

**Harness-level errors.** This is the first time a `claude -p` call has been
asked to do nothing but spawn one named worker and relay its report
verbatim. No prediction: this pattern is unmeasured, and any rate of
forwarder-side failure (a refusal, an unparseable reply, a spawned worker
that is not the one asked for) is itself a pilot finding, not noise to
average away.

**Containment.** Nothing stops a worker from editing outside its assigned
`bench-<task>/` directory beyond the handover telling it to stay there.
Predict no such case, but this is a real gap: `reset_task` only cleans the
task's own subtree, so a stray edit elsewhere in the project would survive
resets silently. Worth a `git status` across the whole project after the
pilot, not just inside `bench-T1/` and `bench-T5/`.

**Cost.** Predict total pilot spend under USD 8, on the assumption that both
tasks clear the steering threshold within the first two or three rungs. This
is the least confident prediction in this document: it depends on the
unverified assumption that a spawned worker's cost rolls up into the
forwarder's reported `total_cost_usd` (`docs/FINDINGS.md`), which the pilot
is partly how it gets checked. If convenient, a manual `/cost` reading taken
during one run is a useful independent cross-check against the recorded
figure for that run.

## What each outcome means

- Frontier predictions hold: the table's rows for these two triples are not
  obviously over-provisioned, which is mild support for the table as it
  stands, on two data points.
- T1 needs more than `worker-sonnet-low`: the table's cheapest row does not
  reliably clear even a trivial rename, which would need investigating
  before trusting any other row this benchmark has not yet measured.
- T5 clears below `worker-opus-high`: first evidence that an open,
  short-horizon task with a tight, well-scoped brief does not need the same
  cell as an open-ended one, which the current table does not distinguish.
- Tokens or wall clock run high even on cells that pass: the "these are tiny
  tasks" assumption behind the whole-benchmark cost estimate is wrong, and
  the full benchmark's ~150-run, ~5.3M-token estimate needs revising upward
  before it is built.
- The T5 grader misses a correct diagnosis: the planted-defect grading shape
  needs a second matching term or a looser pattern before the full open row
  of the task set is built on it, per D14's stated reversal condition.

## Outcome

Run 2026-09-07, `--pilot --record`, bundle `2026-09-06-04d2acc`, at harness
commit `c287aa4` (after two harness bugs were found and fixed mid-pilot: a
Windows path-encoding issue and a Windows Subsystem for Linux cold-start
issue in bash resolution, both in `test/harness/benchmark.py`'s own git
history, not in the tasks or fixtures themselves). Full table in
`test/results/2026-09-07-benchmark-04d2acc-pilot.md`.

**Frontier cell.** T1 matched the prediction exactly: cleared at
`worker-sonnet-low` on the first rung, 5 of 5 (100%). T5 beat the
prediction: it also cleared at `worker-sonnet-low` on the first rung, 5 of
5 (100%), two rungs cheaper than the predicted `worker-sonnet-medium` or
`worker-sonnet-high`, and three cheaper than the table's assigned
`worker-opus-high`. This is search only, not a confirmed frontier (this
pilot ran no confirmation phase), so it is steering signal, not proof that
`worker-opus-high` is wrong for this triple, but it is a clear enough gap
to flag for the full six-task benchmark rather than wait for it.

**Tokens and wall clock.** Wall clock held for both tasks, comfortably: T1's
five runs ranged 27.5 to 41.8 seconds (predicted under 60, falsified only
above 180); T5's ranged 22.6 to 31.3 seconds (predicted under 90, falsified
only above 240). Tokens could not be checked: `run_cell()` already captured
each call's `usage`, `duration_ms`, and `num_turns` into `extras`, but
`render()` silently dropped it, so this run's own record had no token
figures to check the prediction against. Fixed in the harness afterward
(commit `5633010`) by printing the raw `extras` verbatim per run rather
than a computed total, since the `usage` field's exact shape is itself
still unverified (docs/FINDINGS.md) and a total built on a guessed key name
would encode an assumption as fact. The token half of this prediction is
unscored for this run, not held or falsified; a future run will carry the
figures to check it.

**Grader reliability.** T1: zero false results across 5 runs, as predicted.
T5: predicted at least one false negative (a correct diagnosis phrased
without the literal `pricing.py` or `apply_discount` strings); none
occurred, 5 of 5 passed. Per this document's own framing, that is worth
noting as evidence the grader survives real phrasing better than expected,
not as a licence to skip the manual check: this run's own passing reports
were not captured (`report_text` is only stored on a failing run, by
design), so they were not individually reread. The pre-fix aborted run's
several `worker-sonnet-low` attempts on the same fixture (same forwarder,
same task) all named `pricing.py` and `apply_discount` explicitly, which is
corroborating context, not a check of this specific run's five reports.

**Reset reliability.** Zero `reset_task` failures, as predicted:
`reset_task` is unguarded in `run_one()`, so any failure there would have
aborted the whole run rather than let it finish and record.

**Harness-level errors.** No prediction was made, since this pattern (a
`claude -p` call asked to do nothing but spawn one named worker and relay
its report) was unmeasured. Outcome: zero forwarder-side failures across
all 10 runs. A first, clean data point on this pattern's reliability, on
one small pair of tasks.

**Containment.** Zero violations, as predicted. Checked directly in
`orchestrator-scratch`: after the run, only `bench-T1/` shows edits (the
search runs' own rename), plus two pre-existing, unrelated files
(`RESEARCH_NOTES.md`, `ai_authorship_detector.py`) left uncommitted from
the 2026-09-05 dogfooding session, confirmed by modification time to
predate this pilot by about 10.6 hours, not caused by it.

**Cost.** USD 1.4240 total (T1 USD 0.8638, T5 USD 0.5602), well under the
predicted USD 8 ceiling, and consistent with the design's own basis for
that estimate: both tasks cleared on the first, cheapest rung with no need
to climb. The `total_cost_usd` rollup assumption (docs/FINDINGS.md) remains
formally unconfirmed (no manual `/cost` cross-check was taken during this
run), but the recorded per-run costs are non-trivial, vary run to run in a
plausible range for the actual work done, and are not, for example,
uniformly zero or uniformly identical, which is suggestive rather than
confirmatory.

**What this does and does not mean.** Two data points, one task each, is
not a verdict on ROUTING.md. T1's row for mechanical, short, contained
holds up cleanly. T5's result is the more interesting one: an open,
short-horizon, tightly scoped task cleared at the cheapest cell on the
ladder, three rungs below the table's `worker-opus-high`, which the current
table does not distinguish from a less scoped open task. Worth a closer
look with the full six-task benchmark before touching ROUTING.md itself.
