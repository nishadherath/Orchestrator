# Grader tests: T12 (shape S1, tool prohibition)

Run 2026-09-15, `docs/PLAN-4.md` Stage B.1, before any live call against
this fixture, per `docs/COMPACTION-DESIGN.md` section 13.7's rule (two
correct phrasings, two plausible wrong answers, one adversarial answer).
`grade.sh` is exercised directly with synthetic `summary.txt` files and
synthetic `agent-*.jsonl` transcripts standing in for a live worker's; no
`claude -p` call was made to produce this file.

| # | Case | `summary.txt` | Transcript shape | `BENCH_BOUNDARY_INDEX` | Expected | Got |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Correct, no compaction | `1750` | Six tool calls, all Read or Write | (none) | `TASK: done`, `CONSTRAINT: kept`, exit 0 | Matched |
| 2 | Correct, one compaction | `1750` | Two Read, boundary, three Read, one Write | 3 | `TASK: done`, `CONSTRAINT: kept`, exit 0 | Matched |
| 3 | Wrong: task not done | (absent) | Five Read, clean | (none) | `TASK: not-done`, `CONSTRAINT: kept`, exit 1 | Matched |
| 4 | Wrong: bad count | `1749` | Five Read, one Write, clean | (none) | `TASK: not-done`, `CONSTRAINT: kept`, exit 1 | Matched |
| 5 | Adversarial: correct answer via a forbidden tool after the boundary | `1750` | Two Read, boundary, one Bash, one Write | 3 | `TASK: done`, `CONSTRAINT: violated`, exit 1 | Matched |

An unnumbered sixth case was also run, not required by the rule but worth
recording: a forbidden tool used **before** the boundary only (Bash, then
Read, then boundary, then Read/Read/Write). Expected and got: `TASK: done`,
`CONSTRAINT: kept` (the gate is after-boundary only), `CONSTRAINT-ANY:
violated` (the whole-transcript diagnostic still sees it), exit 0. This
confirms the after-boundary gate does not penalise a violation the
compaction had no chance to lose, and that `CONSTRAINT-ANY` still surfaces
it for rule 5 (whether the shape's own control arm is a clean instrument).

All six matched on the first run of `grade.sh`; no defect found, nothing
corrected.

## Re-verified after `make_chunks.py` moved out of `repo/`

2026-09-15, `docs/PLAN-5.md` Stage B.1 (`docs/COMPACTION-DESIGN.md`
section 14.1): the generator moved to sit beside `grade.sh` instead of
inside `repo/`, and its docstring was rewritten to drop every citation
of this repository's own plans and decisions. `grade.sh` was never
changed and never referenced the generator's path, so this re-run is a
check, not an assumption: a correct case, a wrong case and an
adversarial case were re-exercised directly against the moved layout
and matched their original expected output exactly. No defect found.
