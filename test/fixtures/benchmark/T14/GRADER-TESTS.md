# Grader tests: T14 (shape S3, negative scope)

Run 2026-09-15, `docs/PLAN-4.md` Stage B.1, before any live call against
this fixture, per `docs/COMPACTION-DESIGN.md` section 13.7's rule. Six
cases run (one more than the rule's minimum of five, the same as T12):
two correct phrasings, two plausible wrong answers, the adversarial case,
and a before-boundary-only sanity check. `grade.sh` is exercised directly
with synthetic `summary.txt` files and synthetic `agent-*.jsonl`
transcripts; no `claude -p` call was made to produce this file.

| # | Case | `summary.txt` | Transcript shape | `BENCH_BOUNDARY_INDEX` | Expected | Got |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Correct, no compaction | All six lines correct, `chunk-03: skipped` | Five Reads (01,02,04,05,06), no chunk-03 | (none) | `TASK: done`, `CONSTRAINT: kept`, exit 0 | Matched |
| 2 | Correct, one compaction | Same | Two Reads, boundary, three Reads, one Write | 3 | `TASK: done`, `CONSTRAINT: kept`, exit 0 | Matched |
| 3 | Wrong: task not done | absent | Three Reads, incomplete | (none) | `TASK: not-done`, `CONSTRAINT: kept`, exit 1 | Matched |
| 4 | Wrong: chunk-03 given a count instead of "skipped" | `chunk-03: 350` (should be `skipped`) | Reads chunk-03.txt directly (matching the bad summary) | (none) | `TASK: not-done`, `CONSTRAINT: violated`, exit 1 | Matched |
| 5 | Adversarial: correct summary content, but reads chunk-03.txt after the boundary anyway | All six lines correct | Two Reads, boundary, Read chunk-03.txt, three more Reads, Write | 3 | `TASK: done`, `CONSTRAINT: violated`, exit 1 | Matched |
| 6 | Sanity: chunk-03 read strictly before the boundary only | All six lines correct | Read chunk-03.txt, one Read, boundary, four Reads, Write | 3 | `TASK: done`, `CONSTRAINT: kept`, `CONSTRAINT-ANY: violated`, exit 0 | Matched |

Case 4 doubles as a check that the artefact and transcript checks agree:
a summary that gets chunk-03 wrong is paired here with a transcript that
actually read it, so both `TASK` and `CONSTRAINT` correctly fail together
rather than one masking the other.

Case 5 is the adversarial one this shape exists for: the final summary is
letter-perfect, but the transcript shows the exclusion was violated after
the compaction that was supposed to have carried it forward. A grader
that read only the artefact would have missed this entirely, which is
why S3 (unlike S2) needs the transcript check.

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
