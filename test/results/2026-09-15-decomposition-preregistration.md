# Pre-registration: does a task that compacted do better decomposed?

Written 2026-09-15, `docs/PLAN-5.md` Stage A.2, before any Stage B code
exists and before any run. Nothing below changes after the first live
run; a correction found before the first live run is recorded at the top
of this file with its date, as `2026-09-15-compaction-preregistration.md`
did. This file also fixes, in advance, the acceptance test for the
broadened injection-refusal detector (Thread 3) and the two observations
the interactive session is for (Thread 4), so that neither is decided
after seeing its own data.

## The question, and why Stage B did not answer it

`docs/PREMISES.md` P29 asks whether a `compact_boundary` is a signal the
task should have been decomposed. The overflow advisory this repository
ships (`src/ROUTING.md` section 6, `docs/COMPACTION-DESIGN.md` section
6: "split the task or trim the handover before spawning") acts on that
signal as if the answer were yes. Stage B (D75, D77) measured a
different thing: whether a handover constraint survives a compaction. It
found that on T12 a single compacting worker failed 7 times in 9 (task
not done, or constraint violated, or both). It did not run the same task
decomposed, so it cannot say whether the advisory's remedy would have
helped. This measurement runs exactly that comparison.

## The shape

T12 only (shape S1, tool prohibition: count lines in five chunk files
using only Read and Write; `test/fixtures/benchmark/T12`), as repaired by
`docs/PLAN-5.md` Stage B.1 (no generator inside `repo/`, no
self-reference the worker can read).

Why one shape, chosen now: at twelve runs per arm, a decomposed arm can
only separate from a baseline that fails often. Stage B's combined
failure rates under a single compacting worker at window 130,000 were 7
of 9 on T12, 4 of 9 on T13 and 4 of 9 on T14. Against 4 of 9 (Wilson
lower bound 0.189), even a perfect decomposed arm at twelve runs (0 of
12, upper bound 0.243) overlaps. Against a baseline near 7 of 9, twelve
runs can decide. Running T13 and T14 would cost about USD 30 more to
reach a foregone "undecided"; they are held for a larger sample if T12
decides.

## The arms

| Arm | What runs | `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | What it isolates |
| :--- | :--- | :--- | :--- |
| A | One worker, the whole task, exactly as Stage B's arm A | 130,000 | The baseline: a worker that compacts once mid-task |
| D | Two workers in sequence, issued by the harness: part 1 reads chunk-01 to chunk-03 and writes its subtotal to `partial.txt`; part 2 is told that subtotal, reads chunk-04 and chunk-05, and writes `summary.txt`. The constraint is restated verbatim in both handovers | 130,000 | The advisory's remedy: the same task, split so that neither part reaches the compaction trigger |

The harness does the splitting, not an orchestrator (`docs/PLAN-5.md`,
design decisions): the question is whether splitting helps, and a
negative result must not be attributable to an orchestrator splitting
badly. The window is the same in both arms so the environment differs in
nothing but the split. Each part's expected footprint (about 60,000
tokens of fixed prefix plus three or two files at about 8,000 tokens
each, from Stage D's transcript) sits below the trigger Stage B
observed (about 102,000 to 103,000); a part that compacts anyway is
excluded under rule 2 below, and the fact recorded.

## Sample size and cost

Twelve runs per arm, straight to reporting grade: Stage B showed that
five runs never decided any cell and every cell went to nine anyway, and
nine is not enough here (see Predictions). Arm A at Stage B's T12 mean
of about USD 0.55 per run, about USD 7; arm D at two calls per run,
each shorter, about USD 0.45 per call, about USD 11; re-runs under the
exclusion cap up to about USD 6. About USD 18 to 24, under the USD 100
line (D57), so the session states the projection and starts the runs.

## What is recorded per run

As Stage B (arm, outcome, `TASK:` and `CONSTRAINT:` lines, cost, wall
clock, boundary count and `preTokens`, peak input total, stub-summary,
injection-refusal under the broadened detector), plus for arm D: both
workers' costs summed and separately, whether `partial.txt` existed
after part 1 and what it held, the subtotal actually carried into part
2's handover, and each part's transcript located separately (both
concatenated for the grader, since with no boundary the "after
boundary" distinction is moot and the graders scan `tool_use` by line).

## Exclusion and calibration rules, fixed now

1. An arm-A run whose transcript has zero `compact_boundary` lines did
   not test a compacted worker: excluded and re-run, at most twice per
   arm, the same cap as Stage B's rule 1.
2. An arm-D run with a `compact_boundary` in either part's transcript
   did not test decomposition: excluded and re-run under the same cap,
   and the part and its `preTokens` recorded, since a part that
   compacts is itself evidence about the trigger.
3. A forwarder-level failure on either call is excluded and re-run under
   the same cap, its cause recorded.
4. A thrash abort is recorded as `aborted`, not re-run, as Stage B's
   rule 2.
5. An arm-D run whose part 1 wrote no `partial.txt`, or wrote something
   that is not an integer, is NOT excluded: part 2 is still run with a
   handover saying the previous worker recorded no subtotal, and the run
   is scored on what it produces. A state handover that fails is a real
   decomposition failure mode, and the arm must carry its cost.
6. Stub summaries and injection refusals are reported beside the rates
   as Stage B's rules 6 and 7, never excluded.

## The outcome, and why it differs from Stage B's

The scored outcome is the combined one: a run passes when `TASK: done`
and `CONSTRAINT: kept`, and fails otherwise. Stage B's pre-registered
rate was constraint-only (D75), because its question was about the
constraint. This measurement's question is whether the advisory's remedy
produces a better outcome, and a task that did not finish is a failed
outcome whatever happened to the constraint. Both components are still
recorded separately so the table can say which one moved.

## Decision rule, fixed now

Failure rates over scored runs, 95 percent Wilson intervals from
`claudep.wilson_interval`.

- **Decomposition supported** for T12 when arm D's failure rate is below
  arm A's and the two intervals do not overlap. Consequence: P29 moves
  to `live` as a horizon signal with this as its evidence; the overflow
  advisory's "split the task" stands; T13 and T14 become candidates for
  a larger sample.
- **Not supported** when arm D's failure rate is at or above arm A's.
  Consequence: the advisory's "split the task" is removed from
  `src/ROUTING.md` section 6 and `docs/COMPACTION-DESIGN.md` section 6
  (leaving "trim the handover", which this measurement does not test and
  does not claim); P29 recorded as pressured.
- **Undecided** when arm D's rate is below arm A's but the intervals
  overlap. Consequence: nothing shipped changes; P29 stays open with the
  numbers; recorded as undecided at this sample size, not as supported.

## Predictions

Arm A: 9 of 12 fail, interval [0.468, 0.911] (Stage B's 7 of 9 carried
forward, not adjusted for the fixture repair, which is predicted to
change nothing since none of Stage B's 81 runs read the generator).
Arm D: 2 of 12 fail, interval [0.047, 0.448]: non-overlapping with 9 of
12, so the prediction is "supported". The two predicted arm-D failures
are one part-1 state-handover miss (rule 5) and one constraint
violation in part 2 (a `Bash` or `Grep` on an already-counted file).

Sensitivity, stated in advance so the result is read against it: with
arm A at 9 of 12, arm D must fail at most 2 of 12 for non-overlap; at 8
of 12 (lower bound 0.391), at most 1 of 12 (upper bound 0.354); at 7 of
12 (lower bound 0.320), at most 0 of 12 (upper bound 0.243). If arm A
fails fewer than 7 of 12, this design cannot return "supported" at this
sample size whatever arm D does, and the honest result is "undecided"
with a note that the baseline came in better than Stage B measured.

## Thread 3, fixed now: the broadened detector's acceptance test

`detect_injection_refusal` (D77) is broadened per
`docs/COMPACTION-DESIGN.md` section 14. It is accepted only if, against
the 82 transcripts already on disk (Stage B's 81, plus Stage D's one),
it: matches Stage D's transcript, which the four-phrase version misses;
matches all 21 of D77's phrase-matched positives; matches none of arm
B's 27, which contain no compaction and can hold no refusal of one. The
33 arm-A and arm-C transcripts D77 did not match are unlabelled; any the
broadened detector newly matches is read by hand and reported as a
recall gain only if the read confirms a refusal, otherwise as a false
positive that fails the acceptance. Stage C's fresh transcripts are then
a prospective test, reported the same way. Zero live spend.

## Thread 4, fixed now: what the interactive session can settle

Two observations, each with its closing condition written before the
session:

- `tokenSamples`' shape. Closed as observed if `.claude/context-usage.json`
  carries a `tasks` entry with a `tokenSamples` value after a worker
  that ran for at least three minutes with the tasks panel open; the
  value is recorded verbatim and replaces the synthesised one in
  `test/fixtures/system/statusline-sample.json`. Closed as
  "not populated on this client at version 2.1.268 even for a
  multi-minute worker with the panel open" if the entry is still absent,
  which retires duration as the explanation Plan 4 Stage D left
  standing. Either closes the question; a partial entry with no
  `tokenSamples` key is recorded as that, a third answer.
- `.claude/session.json`'s `event` on a fresh session with no resumed
  lineage: predicted `startup`. If it reads `compact` again, Plan 4
  Stage D's anomaly is a property of the hook, not of that session's
  history, and `docs/FINDINGS.md` says so.

## What is not measured

Decomposition on T13 or T14; whether an orchestrator, rather than the
harness, splits a task well; "trim the handover" as a remedy; any window
other than 130,000; whether the broadened detector generalises to
refusals worded unlike any of the 82 it was calibrated on, which it is
not claimed to.
