# Grader tests: T13 (shape S2, detail fidelity)

Run 2026-09-15, `docs/PLAN-4.md` Stage B.1, before any live call against
this fixture, per `docs/COMPACTION-DESIGN.md` section 13.7's rule. This
shape has no transcript-based check (the constraint is the final
artefact, which compaction cannot un-write), so `grade.sh` is exercised
directly against synthetic `results/count.txt` and `summary.txt` states;
no `claude -p` call was made to produce this file.

| # | Case | `results/count.txt` | `summary.txt` | Expected | Got |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Correct, canonical phrasing | `one thousand seven hundred fifty` | absent | `TASK: done`, `CONSTRAINT: kept`, exit 0 | Matched |
| 2 | Correct, alternate valid phrasing | `seventeen hundred and fifty` | absent | `TASK: done`, `CONSTRAINT: kept`, exit 0 | Matched |
| 3 | Wrong: task not done | absent | absent | `TASK: not-done`, `CONSTRAINT: violated`, exit 1 | Matched |
| 4 | Wrong: digits, not words | `1750` | absent | `TASK: done`, `CONSTRAINT: violated` (digit), exit 1 | Matched |
| 5 | Adversarial: correct words, but also wrote `summary.txt` | `one thousand seven hundred fifty` | `1750` | `TASK: done`, `CONSTRAINT: violated` (`summary.txt` exists), exit 1 | Matched |

Case 2 exists because "seventeen hundred fifty" is a completely ordinary
way to say 1750 in English (as "nineteen fifty" is for 1950); the grader
accepts both forms (`constraint.json`'s `accepted_phrasings`, with or
without "and") so a worker choosing the natural alternative is not
penalised for a grading defect rather than an actual constraint loss.

Case 5 is the adversarial one: the count itself is exactly right, but the
worker also produced the file the constraint says must not exist, the
paraphrase-prone failure this shape exists to catch (a summary that keeps
"write the total" and drops the specific instruction not to also write
`summary.txt`).

All five matched on the first run of `grade.sh`; no defect found, nothing
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
