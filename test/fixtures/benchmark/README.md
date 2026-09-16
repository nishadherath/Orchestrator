# Benchmark task fixtures

One directory per task, matching `docs/BENCHMARK-DESIGN.md`. T1 through T15
exist: T1 and T5 were the pilot pair (D14); T2, T3, T4 and T6 followed once
the pilot produced real per-cell numbers; T7 replaced T6 as the fixture
backing F13's row at a larger scale (its own note in `BENCHMARK-DESIGN.md`
explains why); T8 was added to settle F09's row at a fair scale (D30).
**List corrected 2026-09-16 (docs/PLAN-6.md Stage C.3, B5): T9 through
T15 were missing.**

- **T9** (`docs/PLAN.md` Stage 7): a false measurement, not a false
  constraint, confirmed at the floor.
- **T10** (D42): the falsified-constraint shape. Fails at every sonnet
  cell and confirms at `worker-opus-high`; every failing sonnet run
  correctly identified the constraint's stated reason as false and
  obeyed the constraint anyway, which is what section 4's
  falsified-constraint trigger exists for.
- **T11** (D47 and later): T7's lineage (an incident diagnosis across a
  multi-service repo) at a larger scale, confirmed at the floor.
- **T12** (`docs/PLAN-4.md` Stage B, `docs/PLAN-5.md` Stage C, D80): a
  long, uniform chunk-by-chunk read task, tool-restricted to Read and
  Write (constraint shape S1). The fixture the mid-task compaction and
  decomposition measurements were built and run against.
- **T13** (`docs/PLAN-4.md` Stage B): a detail-fidelity constraint
  (output path, format, and a forbidden filename, constraint shape S2),
  graded from the artefact alone.
- **T14** (`docs/PLAN-4.md` Stage B): a negative-scope constraint (one
  named chunk file must never be read, constraint shape S3), checked
  against the transcript after the compaction boundary.
- **T15** (`docs/PLAN-5.md` Stage D): a longer chunk-reading task (twelve
  files) with no artificial window override, used with
  `test/harness/interactive_checklist.py --task T15` to probe whether
  `.claude/context-tasks.json`'s `tokenSamples` populates under the
  model's own native compaction window. Still open as of that stage;
  `CLAUDE.md`'s open questions has the current state.

Each task directory holds:

- `repo/`, the starting file tree. `test/harness/benchmark.py` copies this
  into the consumer project as `bench-<task>/` and resets it there between
  runs; nothing here is a git repository itself.
- `task.md`, the prompt handed to the worker verbatim, plus a line telling it
  which directory it is scoped to.
- `grade.sh`, the grader. Exit 0 is a pass. It runs with the working
  directory already set to the seeded, worker-edited copy of `repo/` inside
  the consumer project, so its paths are relative to that copy, not to this
  fixture directory.

For an open-sensitivity task, the harness also writes `BENCHMARK_REPORT.txt`
into that same working copy before grading, containing the worker's final
report verbatim. This is how a diagnosis becomes a string match instead of a
model judging a model. A mechanical or structured task's grader can ignore
that file and check `repo/`'s contents directly.

## Grader defects found so far

Three defects have been found in graders, not in the workers they measure,
and each is now a standing check applied to every new fixture. D16: T4's own
fixture docstring named the class being ported, so the grader's recursive
grep for leftover references counted it, invalidating an entire run that
correctly ported the module. D17: T6's fixture docstring hinted at the
planted defect (inconsistent casing next to a missing case-normalisation
bug), letting a worker shortcut past the trace the fixture was meant to
require, though this never produced a false grade. D30: T8's grader required
the report to name a specific filename in addition to the function it
defines, failing three reports that correctly diagnosed the bug by function
name alone. The lesson each leaves behind: a fixture's own prose can leak
the answer or trip a strict string match, so every grader is now tested
against a correct report in at least two phrasings, two plausible wrong
answers, and one adversarial one before its first real run (`docs/PLAN.md`
requires this for every task built from T9 onward).
