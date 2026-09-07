# Cost and quality benchmark: design

Specification, not an implementation. Written 2026-09-06 for a Sonnet-class
session to build. Nothing here has been run.

## The question

This repository exists to support one claim: routing a task to the cheapest
sufficient worker cell gets the same quality for less money than not routing.
Nothing in the repository measures that. The fixtures measure whether the
orchestrator picks the cell a human nominated; they cannot tell you whether
that cell was the right one, because the expected cells are Jeb's judgement,
not a measurement.

So the benchmark answers a question the fixtures cannot: **for a given task,
which is the cheapest cell that actually does the job?** Call that the task's
frontier cell.

The counterfactual matters. "Cheaper than not routing" needs a baseline, and
the honest baseline is what a person would otherwise do: run everything on one
capable cell. `worker-opus-high` is the fair stand-in, because it is the cell
the table already reaches for on open work of ordinary size. The benchmark
therefore reports, per task, the frontier cell and the baseline cell, and the
saving is the difference.

## Why deterministic grading, and only deterministic grading

A model grading another model's output is expensive, noisy, and circular here,
since the thing under test is model capability. Every task in this benchmark
must have a grader that is a command with an exit code. Three shapes cover the
sensitivity axis:

| Sensitivity | Task shape | Grader |
| :--- | :--- | :--- |
| Mechanical | A rename, a move, a mechanical transformation across files | The test suite still passes, plus a structural assertion (the old symbol appears nowhere, the new one appears N times) |
| Structured | Implement a function to a stated contract, tests supplied and failing | The supplied tests pass |
| Open | Find a planted defect and report its location | The report names the file and function containing the planted defect |

The open grader is the one that makes this possible at all. Planting a known
defect converts "did it diagnose correctly" from a judgement into a string
match. A task whose quality cannot be reduced to an exit code does not belong
in this benchmark, however representative it feels.

## Task set

Seven tasks, each a fixed starting state in a scratch repository, a prompt,
and a grader command.

| Task | Sensitivity | Horizon | Grader |
| :--- | :--- | :--- | :--- |
| T1 | Mechanical | Short | Rename one symbol, three call sites; suite green and old symbol absent |
| T2 | Mechanical | Long | Same transformation across about thirty files; suite green and count exact |
| T3 | Structured | Short | One function to a written contract, tests supplied |
| T4 | Structured | Long | A module ported to a new interface, existing suite green throughout |
| T5 | Open | Short | One planted defect in a small module; report names file and function |
| T6 | Open | Long | One planted defect reachable only through a chain of three files; same grader |
| T7 | Open | Long | One planted defect shared by four simulated services with different call patterns; reproducible by running the code at varying sizes; two unrelated red herrings; same grader |

T7 exists because T6, run and confirmed twice, was found to be a weaker proxy
for its row than intended: F13, the fixture backing `worker-fable-xhigh`'s
"sustained autonomous investigation" row, describes a multi-service
p99-latency regression traced through traces and profiles, and T6's actual
shape, a defect reachable through a chain of three files in one repository,
is considerably smaller. T7 raises the scale deliberately (four simulated
services, a shared root cause reachable only by noticing which services it
does and does not affect and why, plus two red herrings that require ruling
out rather than a single chain to follow) before the fable-xhigh row is
touched on T6's evidence alone (D19, `docs/DECISIONS.md`).

Blast radius is deliberately not varied. It describes what a wrong answer costs
the owner, not what the worker can do, so it cannot change a grader's exit
code. That is a finding in itself and belongs in the report: **blast radius is
unmeasurable by this method**, and any routing rule that depends on it rests on
judgement, not on evidence this benchmark can supply.

## Protocol: a staircase, not a grid

A full grid of nine routed cells by six tasks by repeats is far more runs than
the question needs. The question is where the frontier is, so search for it.

For each task, starting at the cheapest routed cell and stepping up the cost
ladder (`worker-sonnet-low`, `-medium`, `-high`, `-xhigh`, then `worker-opus-high`,
`-xhigh`, then `worker-fable-xhigh`):

1. Run the cell R_search times. Reset the repository between runs.
2. If the pass rate clears the **steering threshold**, stop. That cell is the
   candidate frontier.
3. Otherwise step up. If the ladder is exhausted, record the task as unsolved
   and note the highest pass rate reached.

Then confirm: run the candidate frontier cell and the cell immediately below it
R_confirm times each, and report both with Wilson intervals.

**Two thresholds, deliberately different** (persona section 6.6). The steering
threshold decides whether to keep climbing, where a false positive costs one
wasted confirmation and a false negative costs the whole ladder above it, so it
runs permissive: **2 of 3**. The reporting threshold decides what the benchmark
claims, where the costs invert, so it runs strict: **the frontier claim requires
the confirmation run's 95 percent Wilson lower bound to exceed 0.7, and the cell
below it to fail its own confirmation at the same bar.** A report never cites the
steering threshold as evidence.

## Sample size, honestly

Three runs is enough to steer and not enough to report. A 3 of 3 result carries
a Wilson interval of [44%, 100%], which supports no claim about capability. Hence
R_search = 3 and R_confirm = 9, with the samples concentrated where the answer
is rather than spread across cells already known to be too weak or needlessly
strong. Nine is the smallest sample size a perfect record can clear the
reporting bar at: nine successes out of nine gives [70.1%, 100%], which clears
it; eight of nine does not, which is the intended strictness (D15; an earlier
R_confirm = 8 could not clear its own bar even at a perfect 8 of 8, which
gives [67.6%, 100%], caught only once the harness was smoke-tested against a
perfect record).

## Cost and wall clock, with the assumptions stated

Revised 2026-09-07 from the pilot (T1 and T5, `test/results/
2026-09-06-benchmark-pilot-preregistration.md`'s Outcome section). What
changed: the cheap end is now measured, not guessed. What did not change:
the uncertainty that actually drives the total, because the pilot tested
the two tasks least likely to need an expensive cell.

- Measured: `worker-sonnet-low` on a short-horizon, contained task (T1,
  mechanical; T5, open) costs USD 0.07 to 0.25 per run, mean about USD 0.15,
  and takes 23 to 42 seconds, mean about 32. Both tasks cleared on the
  cheapest rung, 5 of 5, no climbing. Applied to the real protocol
  (R_search = 3, and R_confirm = 9 with no cell below to also confirm, since
  `worker-sonnet-low` is the ladder's floor): 12 runs per such task, about
  USD 1.80 and 6.4 minutes wall clock.
- Unmeasured: T2, T3, T4, and T6 are new shapes this pilot did not touch,
  and three of the four are long horizon by design, the one axis most
  likely to push a task up the ladder. T2 in particular has no existing
  routing row to even aim at (D13's mechanical long-horizon gap); it is
  the one triple this benchmark could newly justify rather than confirm.
  Nothing about the pilot's result licenses assuming these three clear
  cheaply too.
- So the total is still dominated by a guess, the same one this section
  made before the pilot: assume the three long-horizon tasks each climb
  about 3 rungs before clearing (9 search runs) and confirm at 27 runs
  total (9 search, 9 candidate, 9 the cell below), at a blended USD 5 to 15
  per million tokens and 40k to 80k tokens per run at those tiers (the one
  data point above `worker-sonnet-low` remains the 2026-09-05 dogfood run,
  `worker-fable-xhigh` on an open-ended build: 102.9k tokens, 6 minutes 14
  seconds, no cost recorded for that run). That puts the three long-horizon
  tasks at roughly USD 8 to 32 each, USD 24 to 97 together.
- Total estimate: the three short-horizon tasks (T1, T3, T5) at about USD
  1.80 each, call it USD 5.5 together, plus USD 24 to 97 for the three
  long-horizon tasks, so **about USD 30 to 103** for the full benchmark.
  That is essentially unchanged from the pre-pilot guess of USD 26 to 79,
  not because the pilot found nothing, but because what it found does not
  bear on the part of the estimate that was ever uncertain (the R_confirm
  correction in D15 moved this figure a little further, for an unrelated
  reason: the original arithmetic behind R_confirm = 8 was simply wrong,
  not a finding about any task). The real fix is measuring T2, T4, and T6,
  not extrapolating from T1 and T5.
- Wall clock is still the real constraint. If a long-horizon task needs 25
  runs at several minutes each for the pricier cells, that task alone can
  run 30 minutes to well over an hour; three of them serially is the bulk
  of a working session. This harness deliberately does not run tasks
  concurrently (see the module docstring), so there is no shortcut here
  short of building that, which the original estimate already flagged as
  the more complicated harness.

## Run the pilot first

Do not build the full benchmark from the estimates above. Every number in this
section is a guess, and this project has now twice been corrected by cheap
measurements that contradicted confident reasoning.

**Pilot: T1 and T5 only, full ladder, R = 5, no confirmation phase.** T1 is the
cheapest task and T5 the one whose grader is least proven. Roughly 30 to 50
runs. Its purpose is not to answer the question but to measure the parameters
this design guesses at: tokens and wall clock per run per cell, whether the
planted-defect grader survives the variety of ways workers phrase a report, how often a
cell fails for reasons unrelated to capability, and whether the reset between
runs is reliable. Size the full benchmark from those numbers.

Pre-register the pilot's predictions before running it, in
`test/results/`, as with every measurement since 2026-09-05.

## What this feeds back into

This is the strategic payoff, and it is larger than the cost question.

Today a fixture's `expected_cell` is Jeb's opinion, and `ROW-BACKED` (D13)
requires every routing row to be backed by such a fixture. That makes the whole
table rest on judgement. If the benchmark measures a frontier cell per task
class, then fixture expected cells can be **derived from measurement**, the
routing table can be tuned to the measured frontier rather than to anecdote,
and `ROW-BACKED` becomes a check that every row is grounded in evidence.

That closes the loop the charter has been describing since the beginning:
routing appropriateness has no automatic signal, so build fixtures. The
benchmark is what makes the fixtures themselves defensible.

## What this cannot answer

- **Blast radius.** As above: not reducible to an exit code.
- **Whether the orchestrator picks the frontier cell.** That stays the fixtures'
  job. The benchmark says what the right answer is; the fixtures say whether the
  rubric finds it.
- **Quality above the pass mark.** A grader is a boolean. Two cells that both
  pass may differ in the quality of what they produced, and this method cannot
  see it. Where that matters, it needs a different instrument.
- **Anything about real work.** Six synthetic tasks with plantable defects are
  not Jeb's backlog. The frontier they find is the frontier for tasks that look
  like them.

## Build specification

For the implementer.

- `test/harness/benchmark.py`, Python 3.10, no dependency beyond the standard
  library, matching the conventions in `score_routing.py`.
- Task definitions in `test/fixtures/benchmark/`, one directory per task, each
  holding the starting repository state, `task.md` (the prompt), and
  `grade.sh` (exit code 0 for pass).
- Refuses to run for the same reasons `score_routing.py` refuses: blocking
  environment variables set, `claude` absent, the bundle not installed.
- Resets the scratch repository between runs by `git checkout . && git clean -fd`,
  and asserts the reset worked before the next run rather than trusting it.
- Records per run: task, cell, pass or fail, tokens, cost, wall clock, and the
  grader's output on failure.
- Writes to `test/results/<date>-benchmark-<bundle tag>*.md`, keyed by bundle
  like every other result file, after the collision on 2026-09-06.
- Reports steering decisions and reporting claims separately and labels which
  threshold each used.
