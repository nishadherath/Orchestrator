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

Not yet run. Append after `--pilot --record` completes.
