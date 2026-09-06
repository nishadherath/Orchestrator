# Benchmark task fixtures

One directory per task, matching `docs/BENCHMARK-DESIGN.md`. Currently only
T1 and T5 exist, the pilot pair (D14); the rest of the six-task set is built
once the pilot has produced real per-cell numbers.

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
