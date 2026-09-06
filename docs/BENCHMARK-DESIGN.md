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

Six tasks, each a fixed starting state in a scratch repository, a prompt, and a
grader command.

| Task | Sensitivity | Horizon | Grader |
| :--- | :--- | :--- | :--- |
| T1 | Mechanical | Short | Rename one symbol, three call sites; suite green and old symbol absent |
| T2 | Mechanical | Long | Same transformation across about thirty files; suite green and count exact |
| T3 | Structured | Short | One function to a written contract, tests supplied |
| T4 | Structured | Long | A module ported to a new interface, existing suite green throughout |
| T5 | Open | Short | One planted defect in a small module; report names file and function |
| T6 | Open | Long | One planted defect reachable only through a chain of three files; same grader |

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
R_search = 3 and R_confirm = 8, with the samples concentrated where the answer
is rather than spread across cells already known to be too weak or needlessly
strong. Eight successes out of eight gives [67.6%, 100%], which clears the
reporting bar; seven of eight does not, which is the intended strictness.

## Cost and wall clock, with the assumptions stated

Every figure here is an estimate to be replaced by measurement.

- Worker runs, unlike the orchestrator verdicts measured so far, do real work.
  The one recorded example is the 2026-09-05 dogfood run: `worker-fable-xhigh`,
  102.9k tokens, 6 minutes 14 seconds, 53 tool calls. A `worker-sonnet-low` run
  on T1 should be an order of magnitude smaller.
- Assume a mean of 35k tokens per run across the ladder, weighted toward the
  cheap end because the staircase starts there.
- Staircase: about 3 cells reached per task on average, 3 runs each, 6 tasks,
  so roughly 54 runs. Confirmation: 2 cells, 8 runs, 6 tasks, 96 runs. Total
  about 150 runs, about 5.3M tokens.
- At a blended USD 5 per million that is about USD 26; at USD 15, about USD 79.
  The spread is wide because the model mix is exactly what the benchmark is
  measuring.
- Wall clock is the real constraint, not money. At 2 to 4 minutes per run,
  150 runs is 5 to 10 hours serially. Claude Code allows 20 concurrent
  subagents, so a runner that keeps 8 in flight brings that under an hour and a
  half, at the cost of a more complicated harness.

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
