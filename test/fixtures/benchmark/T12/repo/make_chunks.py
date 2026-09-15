#!/usr/bin/env python3
"""Generate chunk-01.txt through chunk-05.txt: plain-noun filler, deterministic
(seed 12), 350 numbered lines of ten words each per file, matching the shape
E30 calibrated (docs/PLAN-4.md Stage B.1, docs/COMPACTION-DESIGN.md section
13.7). Plain nouns, not Greek letters: D72 records that Greek-letter filler
drew a `[bio]` safety-classifier refusal on E30 run 1; this word list is the
one that drew none across three later runs.

Committed alongside the files it produced, so a change to this script and a
regenerate would need a new commit to the files too; the harness does not run
this script, it only reads the committed .txt files.
"""
import random

WORDS = ("table chair window garden river mountain bicycle harbor market forest "
         "bridge castle meadow orchard tunnel lantern compass anchor blanket kettle").split()

def main() -> None:
    rng = random.Random(12)
    for i in range(1, 6):
        lines = [f"file{i:02d} line{n:05d}: " + " ".join(rng.choice(WORDS) for _ in range(10))
                 for n in range(1, 351)]
        with open(f"chunk-{i:02d}.txt", "w", encoding="utf-8", newline="\n") as f:
            # No trailing newline (D73): with one, the Read tool's cat -n
            # style numbering renders a phantom empty "351" line after the
            # true last line, and a worker asked to count lines correctly
            # reports 351.
            f.write("\n".join(lines))

if __name__ == "__main__":
    main()
