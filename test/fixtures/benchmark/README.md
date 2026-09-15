# Benchmark task fixtures

One directory per task, matching `docs/BENCHMARK-DESIGN.md`. T1 through T8
exist: T1 and T5 were the pilot pair (D14); T2, T3, T4 and T6 followed once
the pilot produced real per-cell numbers; T7 replaced T6 as the fixture
backing F13's row at a larger scale (its own note in `BENCHMARK-DESIGN.md`
explains why); T8 was added to settle F09's row at a fair scale (D30).

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
